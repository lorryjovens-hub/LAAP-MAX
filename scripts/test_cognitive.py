#!/usr/bin/env python3
"""Quick test of LAAP cognitive engine."""
import sys, os, json
sys.path.insert(0, 'D:\\LAAP')
os.environ['OPENAI_API_KEY'] = 'test'

from laap.agi.conscious import GlobalWorkspace, AttentionEngine, ConsciousStream
from laap.agi.self_model import EmergentSelfModel

ws = GlobalWorkspace()
ae = AttentionEngine()
cs = ConsciousStream(workspace=ws, attention=ae)
cs.experience("Hello, I'm Aris.")
frame = cs.current_frame

result = {
    "focus": str(frame.attention_focus),
    "valence": str(frame.emotional_valence),
    "narrative": frame.narrative,
}

with open(os.path.join(os.path.dirname(__file__), '..', '.cognitive_test_result.json'), 'w') as f:
    json.dump(result, f, indent=2)
print(f"OK: focus={result['focus']}, valence={result['valence']}")
