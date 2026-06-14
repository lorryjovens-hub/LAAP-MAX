
import sys, os, json

sys.path.insert(0, r"D:\LAAP")

# Load config
cfg_path = os.path.expanduser("~/.laap/config.json")
with open(cfg_path, 'r') as f:
    cfg = json.load(f)

d = cfg['providers']['deepseek']
os.environ['LAAP_PROVIDER'] = 'deepseek'
os.environ['LAAP_API_KEY'] = d['api_key']
os.environ['LAAP_BASE_URL'] = d.get('base_url', 'https://api.deepseek.com/v1')
os.environ['LAAP_MODEL'] = 'deepseek-v4-flash'

# Step 1: Test LLM directly
from laap.llm.factory import LLMFactory
from laap.llm.provider import Message

f = LLMFactory(default_provider='deepseek', default_model='deepseek-v4-flash')
p = f.get()
print(f"LLM ready: model={p.model}, has_key={bool(p.api_key)}")

m = Message.user("Say hello in one word")
print("Streaming LLM response:")
for ev in p.chat_stream([m]):
    if ev.type == "token":
        print(f"  TOKEN: {ev.content}", end='', flush=True)
    elif ev.type == "done":
        print(f"\n  DONE: content='{ev._content[:50]}'")
        break

print("\n\n--- LLM test complete ---\n")

# Step 2: Test full Agent
from laap.agent.base import Agent, AgentConfig

os.environ['LAAP_API_KEY'] = d['api_key']  # ensure for factory re-init

f2 = LLMFactory(default_provider='deepseek', default_model='deepseek-v4-flash')
a = Agent(
    config=AgentConfig(name="TestAgent", verbose=False),
    llm_factory=f2,
    show_banner=False
)
print(f"Agent ready: tools={a.tool_registry.count}, llm={'YES' if a.llm else 'NO'}")

print("\nCalling agent.chat()...")
r = a.chat("Say hello in one word")
print(f"Response: {r}")
