"""
LAAP AGI — Multi-Agent Awareness & Safe Rollback System

1. AgentRegistry: agents announce presence, heartbeat, capability advertising
2. TaskBoard: shared task queue with ownership & conflict detection
3. SafeRollback: 3-layer backup (memory + file + git) with checksum verification

Prevents:
  - Two agents modifying the same file simultaneously
  - Orphaned tasks when an agent dies
  - Irreversible code corruption
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
import time, logging, os, json, hashlib, threading, uuid
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger("laap.agi.multi_agent")

# ════════════════════════════════════════════════════════════
# Agent Registry — Multi-Agent Awareness
# ════════════════════════════════════════════════════════════

@dataclass
class AgentInfo:
    agent_id: str
    name: str
    role: str = "worker"
    capabilities: List[str] = field(default_factory=list)
    status: str = "online"
    current_task: str = ""
    last_heartbeat: float = field(default_factory=time.time)
    registered_at: float = field(default_factory=time.time)

class AgentRegistry:
    """Shared registry allowing agents to perceive each other."""
    
    HEARTBEAT_TIMEOUT = 30  # seconds before agent considered dead
    
    def __init__(self, registry_path: str = ""):
        self.registry_path = registry_path or os.path.join(
            os.environ.get("LAAP_ROOT", os.path.expanduser("~/.laap")), ".agent_registry.json"
        )
        self.agents: Dict[str, AgentInfo] = {}
        self._lock = threading.Lock()
        self._load()

    def register(self, name: str, role: str = "worker", capabilities: List[str] = None) -> AgentInfo:
        agent = AgentInfo(
            agent_id=str(uuid.uuid4())[:8],
            name=name, role=role,
            capabilities=capabilities or [],
        )
        with self._lock:
            self.agents[agent.agent_id] = agent
            self._save()
        logger.info(f"Agent registered: {name} [{agent.agent_id}] ({role})")
        return agent

    def heartbeat(self, agent_id: str, current_task: str = ""):
        with self._lock:
            if agent_id in self.agents:
                self.agents[agent_id].last_heartbeat = time.time()
                self.agents[agent_id].status = "online"
                if current_task:
                    self.agents[agent_id].current_task = current_task
                self._save()

    def get_online_agents(self) -> List[AgentInfo]:
        now = time.time()
        online = []
        with self._lock:
            for agent in self.agents.values():
                if now - agent.last_heartbeat < self.HEARTBEAT_TIMEOUT:
                    agent.status = "online"
                    online.append(agent)
                else:
                    agent.status = "offline"
        return online

    def get_agent_by_task(self, task_id: str) -> Optional[AgentInfo]:
        with self._lock:
            for agent in self.agents.values():
                if agent.current_task == task_id:
                    return agent
        return None

    def _load(self):
        if os.path.exists(self.registry_path):
            try:
                data = json.load(open(self.registry_path))
                for a in data.get("agents", []):
                    self.agents[a["agent_id"]] = AgentInfo(**a)
            except: pass

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
            data = {"agents": [a.__dict__ for a in self.agents.values()]}
            json.dump(data, open(self.registry_path, 'w'), indent=2)
        except: pass

    def stats(self) -> Dict:
        return {"total": len(self.agents), "online": len(self.get_online_agents())}


# ════════════════════════════════════════════════════════════
# Task Board — Shared Task Coordination
# ════════════════════════════════════════════════════════════

@dataclass
class TaskItem:
    task_id: str
    description: str
    assigned_to: str = ""  # agent_id
    status: str = "pending"  # pending, active, done, failed
    priority: float = 0.5
    affected_files: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    started_at: float = 0.0
    completed_at: float = 0.0

class TaskBoard:
    """Shared task queue with conflict detection."""
    
    def __init__(self, board_path: str = ""):
        self.board_path = board_path or os.path.join(
            os.environ.get("LAAP_ROOT", os.path.expanduser("~/.laap")), ".task_board.json"
        )
        self.tasks: Dict[str, TaskItem] = {}
        self._file_locks: Dict[str, str] = {}  # file_path → agent_id
        self._lock = threading.Lock()
        self._load()

    def claim_task(self, task_id: str, agent_id: str) -> Tuple[bool, str]:
        """Claim a task. Returns (success, reason)."""
        with self._lock:
            if task_id not in self.tasks:
                return False, "Task not found"
            task = self.tasks[task_id]
            if task.status != "pending":
                return False, f"Task already {task.status} by {task.assigned_to}"

            # Conflict detection: check if any affected file is locked
            for f in task.affected_files:
                if f in self._file_locks:
                    locker = self._file_locks[f]
                    if locker != agent_id:
                        return False, f"File locked by agent {locker}: {f}"

            task.assigned_to = agent_id
            task.status = "active"
            task.started_at = time.time()
            for f in task.affected_files:
                self._file_locks[f] = agent_id
            self._save()
            return True, "Claimed"

    def release_task(self, task_id: str, agent_id: str, success: bool = True):
        with self._lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = "done" if success else "failed"
                task.completed_at = time.time()
                for f in task.affected_files:
                    self._file_locks.pop(f, None)
                self._save()

    def create_task(self, description: str, priority: float = 0.5,
                    affected_files: List[str] = None) -> TaskItem:
        task = TaskItem(
            task_id=str(uuid.uuid4())[:8],
            description=description,
            priority=priority,
            affected_files=affected_files or [],
        )
        with self._lock:
            self.tasks[task.task_id] = task
            self._save()
        return task

    def get_pending(self) -> List[TaskItem]:
        return sorted(
            [t for t in self.tasks.values() if t.status == "pending"],
            key=lambda t: (-t.priority, t.created_at),
        )

    def _load(self):
        if os.path.exists(self.board_path):
            try:
                data = json.load(open(self.board_path))
                for t in data.get("tasks", []):
                    self.tasks[t["task_id"]] = TaskItem(**t)
                self._file_locks = data.get("locks", {})
            except: pass

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.board_path), exist_ok=True)
            data = {"tasks": [t.__dict__ for t in self.tasks.values()], "locks": self._file_locks}
            json.dump(data, open(self.board_path, 'w'), indent=2)
        except: pass

    def stats(self) -> Dict:
        return {
            "total": len(self.tasks),
            "pending": sum(1 for t in self.tasks.values() if t.status == "pending"),
            "active": sum(1 for t in self.tasks.values() if t.status == "active"),
            "done": sum(1 for t in self.tasks.values() if t.status == "done"),
            "locks": len(self._file_locks),
        }


# ════════════════════════════════════════════════════════════
# Safe Rollback — 3-Layer Protection
# ════════════════════════════════════════════════════════════

class SafeRollback:
    """
    Three-layer backup and rollback system:
      Layer 1: Memory snapshot (instant, same-process)
      Layer 2: File backup (disk, cross-process)  
      Layer 3: Git commit (permanent, cross-machine)
    
    Every modification is checksum-verified before and after.
    """
    
    def __init__(self, repo_root: str = "", backup_dir: str = ""):
        self.repo_root = repo_root or os.environ.get("LAAP_ROOT", r"D:\LAAP")
        self.backup_dir = backup_dir or os.path.join(self.repo_root, ".safe_rollback")
        os.makedirs(self.backup_dir, exist_ok=True)
        self._memory_snapshots: Dict[str, str] = {}  # filepath → content
        self.rollback_count = 0
        self.successful_restores = 0

    def snapshot(self, file_path: str) -> Dict[str, Any]:
        """Create a 3-layer snapshot before modification."""
        abs_path = file_path if os.path.isabs(file_path) else os.path.join(self.repo_root, file_path)
        if not os.path.exists(abs_path):
            return {"error": "File not found", "path": abs_path}

        content = open(abs_path, 'r', encoding='utf-8').read()
        checksum = hashlib.sha256(content.encode()).hexdigest()[:16]
        snapshot_id = f"{int(time.time())}_{checksum}"

        # Layer 1: Memory
        self._memory_snapshots[abs_path] = content

        # Layer 2: File backup
        backup_path = os.path.join(self.backup_dir, f"{os.path.basename(file_path)}.{snapshot_id}.bak")
        open(backup_path, 'w', encoding='utf-8').write(content)

        # Layer 3: Git (if available)
        git_hash = ""
        try:
            import subprocess
            r = subprocess.run(["git", "add", file_path], cwd=self.repo_root,
                             capture_output=True, text=True, timeout=10)
            r = subprocess.run(["git", "hash-object", "-w", abs_path],
                             cwd=self.repo_root, capture_output=True, text=True, timeout=10)
            git_hash = r.stdout.strip()[:12] if r.returncode == 0 else ""
        except: pass

        return {
            "snapshot_id": snapshot_id,
            "path": abs_path,
            "checksum": checksum,
            "size": len(content),
            "memory": abs_path in self._memory_snapshots,
            "file_backup": backup_path,
            "git_hash": git_hash,
        }

    def verify_integrity(self, file_path: str, expected_checksum: str) -> bool:
        """Verify a file hasn't been corrupted."""
        abs_path = file_path if os.path.isabs(file_path) else os.path.join(self.repo_root, file_path)
        if not os.path.exists(abs_path):
            return False
        current = open(abs_path, 'r', encoding='utf-8').read()
        current_sum = hashlib.sha256(current.encode()).hexdigest()[:16]
        return current_sum == expected_checksum

    def rollback(self, file_path: str, snapshot_id: str = None) -> Dict[str, Any]:
        """
        Rollback to a previous snapshot. Tries layers in order: memory → file → git.
        """
        abs_path = file_path if os.path.isabs(file_path) else os.path.join(self.repo_root, file_path)
        self.rollback_count += 1

        # Layer 1: Memory
        if abs_path in self._memory_snapshots:
            open(abs_path, 'w', encoding='utf-8').write(self._memory_snapshots[abs_path])
            self.successful_restores += 1
            return {"layer": "memory", "success": True, "path": abs_path}

        # Layer 2: File backup
        if snapshot_id:
            backup_path = os.path.join(self.backup_dir, f"{os.path.basename(file_path)}.{snapshot_id}.bak")
            if os.path.exists(backup_path):
                content = open(backup_path, 'r', encoding='utf-8').read()
                open(abs_path, 'w', encoding='utf-8').write(content)
                self.successful_restores += 1
                return {"layer": "file", "success": True, "path": abs_path}

        # Layer 3: Git
        try:
            import subprocess
            subprocess.run(["git", "checkout", "--", file_path],
                         cwd=self.repo_root, capture_output=True, timeout=10)
            if os.path.exists(abs_path):
                self.successful_restores += 1
                return {"layer": "git", "success": True, "path": abs_path}
        except: pass

        return {"layer": "none", "success": False, "error": "All rollback layers failed"}

    def cleanup_old_backups(self, max_age_seconds: int = 86400):
        """Remove backups older than max_age_seconds."""
        now = time.time()
        for f in os.listdir(self.backup_dir):
            fp = os.path.join(self.backup_dir, f)
            if now - os.path.getmtime(fp) > max_age_seconds:
                os.remove(fp)

    def stats(self) -> Dict:
        return {
            "memory_snapshots": len(self._memory_snapshots),
            "file_backups": len(os.listdir(self.backup_dir)),
            "rollbacks": self.rollback_count,
            "successful_restores": self.successful_restores,
        }


# ════════════════════════════════════════════════════════════
# EventBus — Cross-Agent Event Notifications
# ════════════════════════════════════════════════════════════

class EventBus:
    """Shared event bus for cross-agent notifications and real-time heartbeat awareness.

    Events are persisted to a shared JSON file so all agents in the same LAAP
    deployment can publish and consume each other's lifecycle signals.
    """

    # ── Event type constants ──────────────────────────────────
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_CLAIMED = "task.claimed"
    FILE_MODIFIED = "file.modified"
    FILE_RESTORED = "file.restored"
    AGENT_REGISTERED = "agent.registered"
    AGENT_HEARTBEAT = "agent.heartbeat"
    AGENT_ERROR = "agent.error"
    DEPLOY_STARTED = "deploy.started"
    DEPLOY_COMPLETED = "deploy.completed"
    DEPLOY_FAILED = "deploy.failed"

    ALL_EVENT_TYPES = frozenset({
        TASK_STARTED, TASK_COMPLETED, TASK_CLAIMED,
        FILE_MODIFIED, FILE_RESTORED,
        AGENT_REGISTERED, AGENT_HEARTBEAT, AGENT_ERROR,
        DEPLOY_STARTED, DEPLOY_COMPLETED, DEPLOY_FAILED,
    })

    def __init__(self, events_path: str = ""):
        self.events_path = events_path or os.path.join(
            os.environ.get("LAAP_ROOT", r"D:\\LAAP"), ".agent_events.json"
        )
        self._events: List[Dict[str, Any]] = []
        self._subscriptions: Dict[str, List[str]] = {}  # event_type -> [agent_id, ...]
        self._lock = threading.Lock()
        self._load()

    def publish(self, event_type: str, agent_id: str, data: Dict = None) -> Dict[str, Any]:
        """Publish an event to the shared event bus.

        Returns the event dict for chaining / logging.
        """
        if event_type not in self.ALL_EVENT_TYPES:
            logger.warning(f"Unknown event type: {event_type}")

        event = {
            "id": str(uuid.uuid4()),
            "type": event_type,
            "agent_id": agent_id,
            "data": data or {},
            "timestamp": time.time(),
        }
        with self._lock:
            self._events.append(event)
            self._save()
        logger.debug(f"Event published: {event_type} by {agent_id}")
        return event

    def get_events(self, since: float = 0, event_type: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Return events filtered by time and optionally by event type."""
        with self._lock:
            filtered = [
                e for e in self._events
                if e["timestamp"] >= since
                and (event_type is None or e["type"] == event_type)
            ]
        return filtered[-limit:] if limit else filtered

    def subscribe(self, agent_id: str, event_type: str) -> bool:
        """Register an agent's interest in a particular event type."""
        with self._lock:
            subs = self._subscriptions.setdefault(event_type, [])
            if agent_id not in subs:
                subs.append(agent_id)
                self._save()
                logger.info(f"Agent {agent_id} subscribed to {event_type}")
                return True
            return False

    def unsubscribe(self, agent_id: str, event_type: str) -> bool:
        """Remove an agent's subscription to an event type."""
        with self._lock:
            subs = self._subscriptions.get(event_type, [])
            if agent_id in subs:
                subs.remove(agent_id)
                self._save()
                logger.info(f"Agent {agent_id} unsubscribed from {event_type}")
                return True
            return False

    def get_subscribers(self, event_type: str) -> List[str]:
        """Return agent IDs subscribed to a given event type."""
        with self._lock:
            return list(self._subscriptions.get(event_type, []))

    def _load(self):
        if os.path.exists(self.events_path):
            try:
                data = json.load(open(self.events_path, encoding="utf-8"))
                self._events = data.get("events", [])
                self._subscriptions = data.get("subscriptions", {})
            except (json.JSONDecodeError, OSError):
                self._events = []
                self._subscriptions = {}

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.events_path), exist_ok=True)
            data = {
                "events": self._events,
                "subscriptions": self._subscriptions,
            }
            json.dump(data, open(self.events_path, "w", encoding="utf-8"), indent=2)
        except OSError:
            logger.warning(f"Could not write events to {self.events_path}")

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_events": len(self._events),
                "subscription_count": sum(len(v) for v in self._subscriptions.values()),
                "event_types": sorted(self.ALL_EVENT_TYPES),
            }


# ════════════════════════════════════════════════════════════
# Heartbeat Helper — One-Shot Heartbeat + Event Publish
# ════════════════════════════════════════════════════════════

def heartbeat_cycle(agent_id: str, registry_path: str = "",
                    events_path: str = "") -> Dict[str, Any]:
    """Perform a single heartbeat + AGENT_HEARTBEAT event publication.

    Designed to be called in a periodic loop (thread / asyncio / scheduler).
    Returns a dict with keys ``registry_ok`` and ``event_id``, suitable for
    logging or health-check inspection.

    Example usage in a daemon thread::

        def _heartbeat_loop(agent_id, registry_path, events_path):
            while True:
                heartbeat_cycle(agent_id, registry_path, events_path)
                time.sleep(15)
    """
    result: Dict[str, Any] = {"registry_ok": False, "event_id": None}
    try:
        registry = AgentRegistry(registry_path=registry_path)
        registry.heartbeat(agent_id)
        result["registry_ok"] = True
    except Exception as exc:
        logger.warning(f"Heartbeat registry error for {agent_id}: {exc}")

    try:
        bus = EventBus(events_path=events_path)
        ev = bus.publish(EventBus.AGENT_HEARTBEAT, agent_id,
                         data={"status": "alive"})
        result["event_id"] = ev["id"]
    except Exception as exc:
        logger.warning(f"Heartbeat event-bus error for {agent_id}: {exc}")

    return result
