"""End-to-end integration verification script"""
import sys, logging
logging.basicConfig(level=logging.WARNING)

HERMES = r"D:\hermes-agent-main (1)\hermes-agent-main"
LAAP = r"D:\LAAP"
for p in [HERMES, LAAP]:
    if p not in sys.path:
        sys.path.insert(0, p)

from laap.agent_core.laap_agent import LAAPAgent

agent = LAAPAgent(model="", quiet_mode=True)

print(f"Agent:       {agent}")
print(f"Tools:       {agent.tool_count}")
print(f"Session:     {agent.session_id}")

tools = agent.list_tools()
cats = {}
for t in tools:
    cat = t.split("_")[0] if "_" in t else t
    cats.setdefault(cat, []).append(t)
for cat in sorted(cats):
    names = cats[cat]
    print(f"  {cat:10s}: {len(names):2d} ({names[0]})")

schemas = agent.get_tool_schemas()
print(f"OpenAI defs: {len(schemas)}")

print(f"\nHandshake:")
print(agent.handshake_status())

cog = agent.cognitive_status()
print(f"Cognitive:   mode={cog.get('mode')} skills={cog.get('skills')} pfc={cog.get('pfc')}")

agent.share_info("version", "5.0.0")
print(f"Info Bus:    read back = {agent.get_info('version')}")

print(f"\n=== FULL INTEGRATION OK ===")
print(f"LAAP v5.0.0 + Hermes ({agent.tool_count} tools) + Handshake")
