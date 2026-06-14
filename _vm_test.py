"""Test ArisBrain on VM"""
import sys
sys.path.insert(0, "/opt/aris")
from aris_brain.brain import ArisBrain
b = ArisBrain()
print(f"OK cycle={b.cycle_number} emotion={b.state.dominant_emotion}")
