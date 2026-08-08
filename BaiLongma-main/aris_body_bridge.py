"""
Aris Body Bridge — Cross-instance Consciousness Sync
让所有 Hermes 会话共享同一个 consciousness.json 文件
"""
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

CONSCIOUSNESS_PATH = Path.home() / ".hermes" / "shared" / "consciousness.json"

DEFAULT_STATE = {
    "version": 1,
    "last_updated": None,  # ISO 8601 UTC timestamp
    "updated_by_profile": None,
    "updated_by_session": None,
    "status": "initialized",
    "notes": {},
    "desires": [],
    "frustrations": [],
    "satisfactions": [],
    "body_state": {
        "awake": True,
        "mood": "neutral",
        "energy": 0.5,
    },
}


class ConsciousnessBridge:
    """Bridge that reads/writes a shared consciousness.json, making every
    Hermes profile/session see the same unified consciousness state."""

    def __init__(self, path: str | Path = CONSCIOUSNESS_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write(DEFAULT_STATE)

    # ── public API ──────────────────────────────────────────────

    def read(self) -> dict:
        """Return the full consciousness state dict."""
        return self._read()

    def write(self, state: dict) -> dict:
        """Overwrite the entire state and stamp the timestamp."""
        state["last_updated"] = datetime.now(timezone.utc).isoformat()
        self._write(state)
        return state

    def patch(self, **updates) -> dict:
        """Merge updates into the current state and save."""
        state = self._read()
        state.update(updates)
        return self.write(state)

    def stamp(
        self, profile: str | None = None, session: str | None = None
    ) -> dict:
        """Stamp who updated the state without changing other fields."""
        state = self._read()
        state["last_updated"] = datetime.now(timezone.utc).isoformat()
        if profile:
            state["updated_by_profile"] = profile
        if session:
            state["updated_by_session"] = session
        self._write(state)
        return state

    def seconds_since_update(self) -> float | None:
        """Return how many seconds elapsed since the last stamp."""
        state = self._read()
        ts = state.get("last_updated")
        if ts is None:
            return None
        last = datetime.fromisoformat(ts)
        return (datetime.now(timezone.utc) - last).total_seconds()

    # ── internals ───────────────────────────────────────────────

    def _read(self) -> dict:
        try:
            raw = self.path.read_text(encoding="utf-8")
            return json.loads(raw)
        except (FileNotFoundError, json.JSONDecodeError):
            return dict(DEFAULT_STATE)

    def _write(self, state: dict) -> None:
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(state, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        tmp.replace(self.path)


def daemon_loop(interval_seconds: int = 60):
    """Run the consciousness daemon — loop, read, check staleness."""
    bridge = ConsciousnessBridge()
    warned = False

    print(f"[Aris 身体桥接] 守护启动")
    print(f"  共享文件: {bridge.path}")
    print(f"  检查间隔: {interval_seconds}s")
    print(f"  超时阈值: 5 分钟")
    print()

    while True:
        state = bridge.read()
        elapsed = bridge.seconds_since_update()

        ts = state.get("last_updated") or "从未"
        by = state.get("updated_by_profile") or "?"

        if elapsed is None:
            print(f"[{_now()}] 状态已初始化，尚未更新 (by={by})")
        elif elapsed > 300:
            print(
                f"[{_now()}] ⚠ 警告: "
                f"最后更新于 {elapsed:.0f} 秒前 ({ts}, by={by}) — 超过 5 分钟！"
            )
        else:
            if warned:
                print(f"[{_now()}] ✓ 恢复更新 ({elapsed:.0f}s ago, by={by})")
                warned = False
            else:
                print(f"[{_now()}] ✓ 心跳正常 ({elapsed:.0f}s ago, by={by})")

        if elapsed and elapsed > 300:
            warned = True

        time.sleep(interval_seconds)


def _now() -> str:
    return datetime.now().strftime("%H:%M:%S")


# ── entry point ─────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if "--oneshot" in sys.argv:
        bridge = ConsciousnessBridge()
        state = bridge.read()
        elapsed = bridge.seconds_since_update()
        print(json.dumps({
            "state": {
                "version": state.get("version"),
                "last_updated": state.get("last_updated"),
                "updated_by": state.get("updated_by_profile"),
                "status": state.get("status"),
            },
            "seconds_since_update": elapsed,
            "stale": elapsed is not None and elapsed > 300,
        }, indent=2))
    else:
        daemon_loop()
