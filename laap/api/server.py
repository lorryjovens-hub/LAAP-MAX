"""
LAAP — REST API 服务 (Fixed: SSE streaming + full tool support)

提供 HTTP 接口来管理和监控 LAAP Agent。
支持流式输出 (SSE) 和工具调用。
"""
from __future__ import annotations
import json, logging, os, time, asyncio
from typing import Any, AsyncGenerator, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("laap.api")

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel
    HAVE_FASTAPI = True
except ImportError:
    HAVE_FASTAPI = False
    class FastAPI: pass
    class BaseModel: pass
    class HTTPException(Exception): pass
    class Request: pass
    class StreamingResponse: pass


# ── SSE Event helpers (Hermes-compatible) ──

def sse_event(event: str, data: Any) -> str:
    """Format an SSE event string."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def sse_message(event: str, data: Any) -> dict:
    """Return a dict for StreamingResponse media_type."""
    return {"event": event, "data": data}


@dataclass
class StreamEvent:
    """Streaming event — mirrored from Hermes gateway/stream_events.py"""
    type: str  # token, tool_call_start, tool_call_end, done, error, commentary
    data: Any = None
    metadata: dict = field(default_factory=dict)


if not HAVE_FASTAPI:
    app = None
else:
    app = FastAPI(title="LAAP API", version="0.3.0",
                  description="LAAP — Lifeform Autonomous Adaptive Protocol (with SSE streaming)")

    agents: Dict[str, Any] = {}
    from laap.llm.factory import LLMFactory
    factory = LLMFactory()

    class CreateAgentRequest(BaseModel):
        type: str = "codex"
        name: str = "LAAP-Agent"
        provider: str = ""
        model: str = ""
        rsi_enabled: bool = True
        workspace: str = ""

    class ChatRequest(BaseModel):
        message: str
        system_prompt: str = ""
        use_tools: bool = True
        stream: bool = False

    class StepRequest(BaseModel):
        observation: str
        task_success: Optional[float] = None

    @app.get("/health")
    async def health():
        return {"status": "ok", "agents": len(agents), "llm": factory.available}

    @app.post("/agents/create")
    async def create_agent(req: CreateAgentRequest) -> Dict[str, Any]:
        from laap.agent.base import Agent, AgentConfig
        from laap.agent.lifelike import LifelikeAgent, LifelikeConfig
        from laap.agent.codex import CodexAgent, CodexConfig
        if req.type == "codex":
            config = CodexConfig(name=req.name, workspace_dir=req.workspace)
            agent = CodexAgent(config=config, llm_factory=factory)
        elif req.type == "lifelike":
            config = LifelikeConfig(name=req.name, rsi_enabled=req.rsi_enabled)
            agent = LifelikeAgent(config=config, llm_factory=factory)
        else:
            config = AgentConfig(name=req.name)
            agent = Agent(config=config, llm_factory=factory)
        agents[agent.id] = agent
        return {"agent_id": agent.id, "name": agent.config.name,
                "type": req.type, "status": agent.status()}

    @app.get("/agents")
    async def list_agents() -> List[Dict[str, Any]]:
        return [{"id": aid, "name": a.config.name, "alive": a.alive, "steps": a.step_count}
                for aid, a in agents.items()]

    @app.get("/agents/{agent_id}")
    async def get_agent(agent_id: str) -> Dict[str, Any]:
        agent = agents.get(agent_id)
        if not agent: raise HTTPException(404, "Agent not found")
        if hasattr(agent, 'complete_status'):
            return agent.complete_status()
        return agent.status()

    @app.post("/agents/{agent_id}/chat")
    async def chat_with_agent(agent_id: str, req: ChatRequest) -> Any:
        """Chat with agent. If req.stream=True, returns SSE streaming response."""
        agent = agents.get(agent_id)
        if not agent: raise HTTPException(404, "Agent not found")

        if req.stream:
            return StreamingResponse(
                _stream_agent_chat(agent, req.message, req.system_prompt, req.use_tools),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive",
                         "X-Accel-Buffering": "no"}
            )

        # Non-streaming fallback
        response = agent.chat(req.message, req.system_prompt,
                              tools=agent.get_tool_defs() if req.use_tools else None)
        return {"response": response, "steps": agent.step_count}

    async def _stream_agent_chat(agent, message: str, system_prompt: str = "",
                                  use_tools: bool = True) -> AsyncGenerator[str, None]:
        """SSE streaming generator — Hermes-compatible events."""
        start = time.time()
        yield sse_event("start", {"agent_id": agent.id})

        # Build tool definitions
        tools = agent.get_tool_defs() if use_tools and hasattr(agent, 'get_tool_defs') else None

        # Use the agent's chat_stream if available, else simulate
        if hasattr(agent, 'chat_stream'):
            async for event in agent.chat_stream(message, system_prompt, tools=tools):
                if event.type == "token":
                    yield sse_event("token", {"content": event.data})
                elif event.type == "tool_call":
                    yield sse_event("tool_call", event.data)
                elif event.type == "tool_result":
                    yield sse_event("tool_result", event.data)
                elif event.type == "error":
                    yield sse_event("error", {"message": str(event.data)})
        else:
            # Fallback: use synchronous agent.chat and yield full response
            response = agent.chat(message, system_prompt, tools=tools)
            yield sse_event("token", {"content": str(response)})
            yield sse_event("token", {"content": "\n"})

        elapsed = time.time() - start
        yield sse_event("done", {"elapsed": elapsed, "agent_id": agent.id})

    @app.post("/agents/{agent_id}/stream")
    async def stream_chat(agent_id: str, req: ChatRequest) -> Any:
        """Shortcut: SSE streaming chat endpoint (same as /chat with stream=true)."""
        req.stream = True
        return await chat_with_agent(agent_id, req)

    # ── Direct streaming endpoint (no agent needed) ──
    class DirectChatRequest(BaseModel):
        message: str
        system_prompt: str = "You are a helpful AI assistant."
        model: str = ""
        stream: bool = True

    @app.post("/v1/chat/completions")
    async def direct_chat(req: DirectChatRequest) -> Any:
        """OpenAI-compatible streaming endpoint."""
        from laap.llm.provider import LLMFactory as ProvFactory
        provider = ProvFactory().create()
        if not req.stream:
            full = ""
            async for chunk in provider.achat_stream(
                [{"role": "system", "content": req.system_prompt},
                 {"role": "user", "content": req.message}]
            ):
                if chunk.type == "token":
                    full += chunk.data
            return {"choices": [{"message": {"content": full}}]}

        async def _gen():
            async for chunk in provider.achat_stream(
                [{"role": "system", "content": req.system_prompt},
                 {"role": "user", "content": req.message}]
            ):
                if chunk.type == "token":
                    yield f"data: {json.dumps({'choices': [{'delta': {'content': chunk.data}}]})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(_gen(), media_type="text/event-stream",
                                  headers={"Cache-Control": "no-cache"})

    @app.post("/agents/{agent_id}/step")
    async def step_agent(agent_id: str, req: StepRequest) -> Dict[str, Any]:
        agent = agents.get(agent_id)
        if not agent: raise HTTPException(404, "Agent not found")
        from laap.agent.lifelike import LifelikeAgent
        if isinstance(agent, LifelikeAgent):
            return agent.step(req.observation, req.task_success)
        return {"error": "LifelikeAgent required for step"}

    @app.post("/agents/{agent_id}/rsi")
    async def trigger_rsi(agent_id: str) -> Dict[str, Any]:
        agent = agents.get(agent_id)
        if not agent: raise HTTPException(404, "Agent not found")
        if hasattr(agent, 'rsi') and agent.rsi:
            proposal = agent.rsi.step(agent, force=True)
            return {"proposal": proposal.to_dict() if proposal else None,
                    "rsi_status": agent.rsi.status(),
                    "fitness": agent.evaluator.report(agent) if hasattr(agent, 'evaluator') else None}
        return {"error": "RSI not enabled on this agent"}

    @app.get("/agents/{agent_id}/tools")
    async def list_tools(agent_id: str) -> List[Dict[str, Any]]:
        agent = agents.get(agent_id)
        if not agent: raise HTTPException(404, "Agent not found")
        return [{"name": t.name, "description": t.description[:60], "category": t.category}
                for t in agent.tool_registry.list()]

    @app.on_event("startup")
    async def startup():
        logger.info("LAAP API 服务启动 (SSE streaming enabled)")


def serve(host: str = "127.0.0.1", port: int = 8000):
    """启动 API 服务"""
    if not HAVE_FASTAPI:
        print("需要安装 fastapi 和 uvicorn: pip install fastapi uvicorn")
        return
    import uvicorn
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    serve()
