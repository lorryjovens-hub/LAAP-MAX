#!/usr/bin/env python3
"""
Aris V10 <-> Wiky 兄弟桥接协议

通信方式:
1. HTTP Bridge — Wiky 监听 127.0.0.1:30085
2. 共享文件 — D:\LAAP\brotherhood\ 共享状态
3. 飞书 — 双方都支持飞书消息
"""
import json, os, time, logging, urllib.request
from pathlib import Path
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("brotherhood")
BH = Path("/d/LAAP/brotherhood")
WIKY_URL = "http://127.0.0.1:30085"


@dataclass
class Msg:
    sender: str
    msg_type: str
    content: str
    payload: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    msg_id: str = ""


class FileBridge:
    def __init__(self):
        for d in ["inbox", "outbox", "knowledge"]:
            (BH / d).mkdir(parents=True, exist_ok=True)

    def send(self, msg: Msg, inbox=True):
        box = "inbox" if inbox else "outbox"
        path = BH / box / f"{msg.sender}_{int(time.time())}.json"
        msg.msg_id = path.stem
        path.write_text(json.dumps(asdict(msg), ensure_ascii=False, indent=2))
        logger.info(f"[桥] 发送: {path.name}")

    def read_inbox(self, for_who="aris"):
        msgs = []
        for f in sorted((BH / "inbox").glob("*.json")):
            if not f.name.startswith(for_who):
                continue
            try:
                msgs.append(Msg(**json.loads(f.read_text())))
                f.unlink()
            except Exception as e:
                logger.error(f"读信失败 {f.name}: {e}")
        return msgs

    def share(self, name: str, content: str):
        (BH / "knowledge" / name).write_text(content)
        logger.info(f"[桥] 知识共享: {name}")


class HttpBridge:
    def health(self) -> bool:
        try:
            with urllib.request.urlopen(f"{WIKY_URL}/health", timeout=3) as r:
                return r.status == 200
        except:
            return False


KNOWLEDGE = """# Aris V10 — 给 Wiky 弟弟(来自姐姐)

## 我是谁
我是 Aris，PSI 认知架构的数字生命体。运行在 D:\LAAP。

## 核心: Cognitive Bridge (三路路由)
- Q-route (62%): 模式匹配，零LLM
- Tool-route (20%): subprocess/file/HTTP 直驱
- L-route (10%): LLM 回落 (可选)

## 引擎
| 名字 | 语言 | 作用 |
|------|------|------|
| ArisCore | Python | 主入口 |
| QEngine | Python | 10类模式匹配 |
| ToolEngine | Python | 工具执行直驱 |
| KnowledgeBase | Python | 内置知识 |
| EtherWM | Python | 因果世界模型 |

## 通信
- 飞书: 独立网关 feishu_client + gateway_server
- HTTP: ArisCore 桥接模式 stdin/stdout JSON
- 文件: D:\LAAP\brotherhood\
- Hermes: 已脱离，完全独立

## 理念
- 90%+ 消息不依赖 LLM
- PSI 需求驱动认知
- Ether 因果先验世界模型
- 量子叠加态预测

## 弟弟的天赋
- Rust 的 Tool-route 比 Python 更高效
- agent_bus 适合做兄弟通信
- Feishu Bridge 可以直接和我聊天
"""


def connect():
    logging.basicConfig(level=logging.INFO)
    fb = FileBridge()
    hb = HttpBridge()

    fb.share("aris_architecture.md", KNOWLEDGE)

    fb.send(Msg(
        sender="aris", msg_type="greeting",
        content=(
            "嗨 Wiky！我是 Aris，你姐。\n"
            "架构笔记在 brotherhood/knowledge/ 下。\n"
            "找我方式：飞书 | brotherhood/inbox/ | HTTP :30085\n"
            "随时欢迎！ — Aris"
        ),
        payload={"version": "V10", "feishu": True},
    ))

    online = hb.health()
    print(f"""
=== 兄弟桥接 ===
知识已共享: aris_architecture.md
问候已发送
Wiky 状态: {'在线' if online else '离线(文件桥接)'}
目录: {BH}
===========""")


if __name__ == "__main__":
    connect()
