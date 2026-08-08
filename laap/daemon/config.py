"""laap.daemon — 配置管理。"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class DaemonConfig:
    """守护进程配置。"""

    # 进程标识
    agent_id: str = "aris"
    daemon_port: int = 19420  # LAAP 谐音

    # 缓存路径
    l0_cache_path: str = ""
    l1_cache_path: str = ""

    # 缓存参数
    l0_max_size: int = 1000
    l0_ttl: int = 3600
    l1_max_size: int = 2000
    l1_ttl: int = 7200
    l1_threshold: float = 0.85

    # 持久化
    auto_save_interval: int = 60  # 自动保存间隔（秒）

    # 健康检查
    health_check_interval: int = 15
    max_restart_attempts: int = 3

    # 日志
    log_level: str = "INFO"
    log_file: str = ""

    def __post_init__(self):
        state_dir = Path(__file__).parent / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        if not self.l0_cache_path:
            self.l0_cache_path = str(state_dir / "l0_cache.json")
        if not self.l1_cache_path:
            self.l1_cache_path = str(state_dir / "l1_cache.json")
        if not self.log_file:
            self.log_file = str(state_dir / "daemon.log")

    @classmethod
    def from_file(cls, path: str) -> DaemonConfig:
        """从 JSON 配置文件加载。"""
        p = Path(path)
        if not p.exists():
            return cls()
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "daemon_port": self.daemon_port,
            "l0_cache_path": self.l0_cache_path,
            "l1_cache_path": self.l1_cache_path,
            "auto_save_interval": self.auto_save_interval,
            "health_check_interval": self.health_check_interval,
            "max_restart_attempts": self.max_restart_attempts,
            "log_level": self.log_level,
        }