"""更新 .task_board.json：将已完成任务标记为 completed（与 Trae 现有状态值对齐）"""
import json

BOARD = r"D:\LAAP\.task_board.json"

DONE_MARKERS = [
    "[P1]", "[P2]",
    "[P3] 1v1", "[P3] P2P", "[P3] 社区身份",
]

def main():
    with open(BOARD, "r", encoding="utf-8") as f:
        board = json.load(f)
    changed = 0
    for t in board["tasks"]:
        desc = t.get("description", "")
        if t.get("status") == "completed":
            continue
        if any(m in desc for m in DONE_MARKERS):
            t["status"] = "completed"
            t["completed_at"] = 1785542400.0  # 2026-08-01 08:00 CST 近似
            changed += 1
    with open(BOARD, "w", encoding="utf-8") as f:
        json.dump(board, f, ensure_ascii=False, indent=2)
    from collections import Counter
    print(f"updated={changed}")
    print("status:", dict(Counter(t["status"] for t in board["tasks"])))

if __name__ == "__main__":
    main()
