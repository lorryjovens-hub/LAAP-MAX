"""Web Replica Harness - FastAPI 入口与 Celery 编排"""

import asyncio
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, make_asgi_app

from src.api.models import ReplicationRequest, ReplicationResponse, TaskStatus
from src.api.routes import router as api_router
from src.config import get_settings
from src.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)

# Prometheus 指标
REPLICATION_COUNTER = Counter(
    "harness_replications_total",
    "Total visual replication tasks",
    ["framework", "status"],
)
REPLICATION_LATENCY = Histogram(
    "harness_replication_duration_seconds",
    "Time spent on replication",
    ["framework"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时初始化意识大脑，关闭时清理资源"""
    logger.info("🧠 Consciousness Harness 启动中...")
    
    # 初始化记忆层
    from src.consciousness.memory.design_system import DesignSystemMemory
    app.state.design_memory = DesignSystemMemory()
    await app.state.design_memory.initialize()
    
    # 初始化沙箱池
    from src.sandbox.executor import SandboxPool
    app.state.sandbox_pool = SandboxPool()
    await app.state.sandbox_pool.initialize()
    
    logger.info("✅ Harness 意识大脑已上线")
    yield
    
    # 清理
    logger.info("🛑 正在关闭 Harness 意识大脑...")
    await app.state.design_memory.close()
    await app.state.sandbox_pool.close()
    logger.info("✅ 资源已清理")


app = FastAPI(
    title="Web Replica Harness",
    description="Consciousness-Driven Visual Replication Engine for AGI",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not settings.is_production else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus 指标端点
app.mount("/metrics", make_asgi_app())

# API 路由
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "consciousness": "online",
    }


@app.post("/api/v1/replicate", response_model=ReplicationResponse)
async def replicate_website(
    image: UploadFile = File(..., description="网页截图，支持 PNG/JPG/WebP"),
    video: UploadFile = File(None, description="交互录屏视频，支持 MP4/WebM"),
    config: str = Form("{}", description="JSON 配置字符串"),
):
    """
    核心复现接口：上传图片和视频，Harness 意识大脑完美复现网页
    """
    task_id = str(uuid.uuid4())
    
    try:
        import json
        parsed_config = ReplicationRequest(**json.loads(config))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"配置解析失败: {str(e)}")
    
    # 保存上传文件
    upload_dir = Path(settings.upload_dir) / task_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    image_path = upload_dir / image.filename
    with open(image_path, "wb") as f:
        f.write(await image.read())
    
    video_path = None
    if video:
        video_path = upload_dir / video.filename
        with open(video_path, "wb") as f:
            f.write(await video.read())
    
    # 提交异步任务到 Celery
    from src.consciousness.execution.orchestrator import ReplicationOrchestrator
    orchestrator = ReplicationOrchestrator()
    
    # 启动复现流水线
    asyncio.create_task(
        orchestrator.run_replication_pipeline(
            task_id=task_id,
            image_path=str(image_path),
            video_path=str(video_path) if video_path else None,
            config=parsed_config,
        )
    )
    
    REPLICATION_COUNTER.labels(
        framework=parsed_config.framework, status="started"
    ).inc()
    
    logger.info(f"[Task {task_id}] 复现任务已提交", extra={
        "task_id": task_id,
        "framework": parsed_config.framework,
        "has_video": video_path is not None,
    })
    
    return ReplicationResponse(
        task_id=task_id,
        status="queued",
        message="Harness 意识大脑已接收任务，正在解析视觉输入...",
        estimated_seconds=120 if video_path else 60,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        reload=not settings.is_production,
    )
