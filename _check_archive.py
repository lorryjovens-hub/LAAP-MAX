"""Check if another session recorded anything"""
import sys, json
sys.path.insert(0, "D:/LAAP")
from aris_brain.memory.archive import ConversationArchive

a = ConversationArchive()
total = a.total_exchanges()
print(f"Total exchanges in archive: {total}")
recent = a.recall_recent(5)
for e in recent:
    print(f'  [{e["role"]}] {e["content"][:80]}')
print(f"\nArchive path: archive/conversations.db")
