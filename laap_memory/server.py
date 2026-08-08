"""
laap_memory/server.py — 同步服务器

WebSocket 服务，让不同设备上的同一个数字生命体自动同步记忆。

协议：
  客户端连接后发送 EntityAuth 消息认证身份。
  之后可双向同步记忆变更。

消息格式（JSON）：
  {"type": "auth", "entity_id": "...", "device_id": "...", "key": "..."}
  {"type": "pull", "since_version": 0}
  {"type": "push", "memories": [...]}
  {"type": "sync_result", "pulled": [...], "pushed": 5}
  {"type": "ping"} / {"type": "pong"}
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Optional

from .models import MemoryEntry, MemoryType, DeviceInfo
from .vault import MemoryVault
from .sync import SyncEngine

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
    HAS_WS = True
except ImportError:
    HAS_WS = False

log = logging.getLogger("laap-memory.server")


class SyncServer:
    """记忆同步 WebSocket 服务器

    每个已认证的客户端可以：
    - 拉取远程记忆变更
    - 推送本地记忆变更
    - 自动合并冲突
    """

    def __init__(self, vault: MemoryVault, host: str = "0.0.0.0", port: int = 9750,
                 auth_keys: dict[str, str] = None):
        self.vault = vault
        self.host = host
        self.port = port
        self.auth_keys = auth_keys or {}  # entity_id -> api_key 映射
        self.clients: dict[str, WebSocketServerProtocol] = {}  # device_id -> ws
        self._server = None

    async def start(self):
        """启动 WebSocket 服务器"""
        if not HAS_WS:
            log.error("websockets 库未安装，无法启动同步服务器")
            raise RuntimeError("pip install websockets")

        self._server = await websockets.serve(
            self._handle_client,
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=10,
        )
        log.info(f"Sync server listening on ws://{self.host}:{self.port}")
        return self

    async def stop(self):
        """停止服务器"""
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            log.info("Sync server stopped")

    async def _handle_client(self, websocket: WebSocketServerProtocol):
        """处理客户端连接"""
        device_id = None
        entity_id = None
        peer = websocket.remote_address

        try:
            log.info(f"New connection from {peer}")
            async for message in websocket:
                try:
                    data = json.loads(message)
                    msg_type = data.get("type", "")

                    if msg_type == "auth":
                        entity_id = data.get("entity_id", "")
                        device_id = data.get("device_id", "")
                        key = data.get("key", "")

                        # 验证身份
                        expected_key = self.auth_keys.get(entity_id, "")
                        if expected_key and key != expected_key:
                            await self._send(websocket, {
                                "type": "auth_error",
                                "message": "Invalid key"
                            })
                            continue

                        # 注册设备
                        dev_info = DeviceInfo(
                            device_id=device_id,
                            name=data.get("device_name", ""),
                            priority=data.get("priority", 100),
                        )
                        self.vault.register_device(dev_info)
                        self.clients[device_id] = websocket

                        await self._send(websocket, {
                            "type": "auth_ok",
                            "device_id": device_id,
                            "entity_id": entity_id,
                            "server_time": time.time(),
                        })
                        log.info(f"Device authenticated: {device_id} ({entity_id})")

                    elif msg_type == "pull":
                        if not entity_id:
                            await self._send(websocket, {
                                "type": "error",
                                "message": "Not authenticated"
                            })
                            continue

                        since_version = data.get("since_version", 0)
                        limit = data.get("limit", 500)

                        sync_engine = SyncEngine(self.vault, DeviceInfo(device_id=device_id))
                        entries = self.vault.get_newer_than(entity_id, since_version, limit)

                        await self._send(websocket, {
                            "type": "pulled",
                            "memories": [e.to_dict() for e in entries],
                            "since_version": since_version,
                            "count": len(entries),
                        })

                    elif msg_type == "push":
                        if not entity_id:
                            await self._send(websocket, {
                                "type": "error",
                                "message": "Not authenticated"
                            })
                            continue

                        memories_data = data.get("memories", [])
                        remote_device = data.get("source_device", device_id)
                        merge_count = 0

                        sync_engine = SyncEngine(self.vault, DeviceInfo(device_id=device_id))
                        for mem_data in memories_data:
                            entry = MemoryEntry.from_dict(mem_data)
                            local = self.vault.get_by_id(entry.id)
                            if local is None:
                                self.vault.store(entry, sign=False)
                                merge_count += 1
                            else:
                                winner = sync_engine.resolve_conflict(local, entry)
                                if winner.id != local.id or winner.version != local.version:
                                    winner.version = max(local.version, entry.version) + 1
                                    self.vault.store(winner, sign=False)
                                    merge_count += 1

                        await self._send(websocket, {
                            "type": "pushed_ack",
                            "received": len(memories_data),
                            "merged": merge_count,
                        })

                    elif msg_type == "ping":
                        await self._send(websocket, {"type": "pong", "server_time": time.time()})

                    else:
                        await self._send(websocket, {
                            "type": "error",
                            "message": f"Unknown message type: {msg_type}"
                        })

                except json.JSONDecodeError:
                    await self._send(websocket, {
                        "type": "error",
                        "message": "Invalid JSON"
                    })

        except websockets.exceptions.ConnectionClosed:
            log.info(f"Client disconnected: {device_id or peer}")
        finally:
            if device_id and device_id in self.clients:
                del self.clients[device_id]

    async def _send(self, ws: WebSocketServerProtocol, data: dict):
        """发送 JSON 消息"""
        await ws.send(json.dumps(data, ensure_ascii=False, default=str))

    async def _broadcast(self, entity_id: str, exclude_device: str, data: dict):
        """广播给指定实体的所有其他设备"""
        for dev_id, ws in list(self.clients.items()):
            if dev_id != exclude_device:
                try:
                    await self._send(ws, data)
                except Exception:
                    pass


class SyncClient:
    """同步客户端——连接到远程 SyncServer"""

    def __init__(self, vault: MemoryVault, entity_id: str,
                 device_info: DeviceInfo, api_key: str = ""):
        self.vault = vault
        self.entity_id = entity_id
        self.device = device_info
        self.api_key = api_key
        self.ws = None
        self.connected = False

    async def connect(self, url: str) -> bool:
        """连接到同步服务器"""
        if not HAS_WS:
            log.error("websockets 库未安装")
            return False

        try:
            self.ws = await websockets.connect(url, ping_interval=30)
            # 发送认证
            await self.ws.send(json.dumps({
                "type": "auth",
                "entity_id": self.entity_id,
                "device_id": self.device.device_id,
                "device_name": self.device.name,
                "priority": self.device.priority,
                "key": self.api_key,
            }))

            response = await asyncio.wait_for(self.ws.recv(), timeout=5)
            data = json.loads(response)
            if data.get("type") == "auth_ok":
                self.connected = True
                log.info(f"Connected to sync server as {self.device.device_id}")
                return True
            else:
                log.error(f"Auth failed: {data}")
                return False

        except Exception as e:
            log.error(f"Connection failed: {e}")
            return False

    async def pull(self, since_version: int = 0) -> list[MemoryEntry]:
        """从服务器拉取记忆"""
        if not self.connected or not self.ws:
            raise RuntimeError("Not connected")

        await self.ws.send(json.dumps({
            "type": "pull",
            "since_version": since_version,
        }))

        # 循环读取，跳过广播消息，直到拿到响应
        while True:
            response = await asyncio.wait_for(self.ws.recv(), timeout=10)
            data = json.loads(response)

            if data.get("type") == "pulled":
                entries = [MemoryEntry.from_dict(m) for m in data.get("memories", [])]
                # 合并到本地 Vault
                for e in entries:
                    local = self.vault.get_by_id(e.id)
                    if local is None:
                        self.vault.store(e, sign=False)
                return entries
            # 忽略广播消息，继续等待响应
            continue

    async def push(self, since_version: int = 0, limit: int = 500) -> int:
        """推送本地记忆到服务器"""
        if not self.connected or not self.ws:
            raise RuntimeError("Not connected")

        entries = self.vault.get_newer_than(self.entity_id, since_version, limit)
        if not entries:
            return 0

        await self.ws.send(json.dumps({
            "type": "push",
            "memories": [e.to_dict() for e in entries],
            "source_device": self.device.device_id,
        }, ensure_ascii=False, default=str))

        response = await asyncio.wait_for(self.ws.recv(), timeout=30)
        data = json.loads(response)
        return data.get("merged", 0)

    async def sync(self) -> dict:
        """执行一次完整同步（先拉后推）"""
        sync_state = self.vault.get_sync_state(f"remote:{self.entity_id}")
        since_version = sync_state.get("last_version", 0)

        pulled = await self.pull(since_version)
        pushed = await self.push(since_version)

        # 更新同步状态
        max_version = max(
            (e.version for e in pulled),
            default=since_version
        )
        self.vault.update_sync_state(f"remote:{self.entity_id}", max_version)

        return {
            "pulled": len(pulled),
            "pushed": pushed,
            "since_version": since_version,
        }

    async def close(self):
        """关闭连接"""
        if self.ws:
            await self.ws.close()
            self.connected = False