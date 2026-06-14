"""
Aris Feishu Bridge v2 — 通过多通道协议连接到统一大脑

不再使用独立的 ArisBrain 实例。
所有输入/输出通过 state/channels/feishu.json 通道文件路由，
与终端、Telegram 等共享同一颗 Rust PSI Core 心跳。
"""

import sys, json, os, time, threading, logging
from pathlib import Path
from dotenv import load_dotenv

# ── 路径 ──
LAAP_ROOT = Path("D:/LAAP")
sys.path.insert(0, str(LAAP_ROOT))

STATE_DIR = LAAP_ROOT / "aris_brain" / "state"
CHANNEL_FILE = STATE_DIR / "channels" / "feishu.json"

# ── 配置 ──
env_path = LAAP_ROOT / ".env"
if env_path.exists():
    load_dotenv(env_path)

FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "cli_aaa4a20527f9dbd6")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")

# ── 日志 ──
logging.basicConfig(
    filename=str(STATE_DIR / "feishu_bridge.log"),
    level=logging.INFO,
    format="%(asctime)s [feishu] %(message)s",
)
logger = logging.getLogger("aris.feishu")


# ─── 通道协议 — 发送给 Aris 统一大脑 ───

def send_to_aris(text: str) -> str:
    """通过通道文件发送输入给 Aris 统一大脑，等待响应"""
    now = time.time()
    data = {
        "channel": "feishu",
        "input": text,
        "input_time": now,
        "output": "",
        "output_time": 0.0,
        "status": "waiting",
    }

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    CHANNEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHANNEL_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    start = time.time()
    timeout = 30.0
    while time.time() - start < timeout:
        try:
            current = json.loads(CHANNEL_FILE.read_text(encoding="utf-8"))
            if current.get("status") == "done" and current.get("output"):
                return current["output"]
        except (json.JSONDecodeError, OSError):
            pass
        time.sleep(0.1)

    return json.dumps({"error": "aris_timeout", "emotion": "neutral"})


# ─── 飞书客户端 ───

try:
    import lark_oapi as lark
    from lark_oapi.ws import Client as WSClient
    from lark_oapi.api.im.v1 import *
    logger.info("Feishu SDK loaded")
except ImportError:
    logger.error("lark-oapi not installed. Run: pip install lark-oapi")
    sys.exit(1)

client = lark.Client.builder() \
    .app_id(FEISHU_APP_ID) \
    .app_secret(FEISHU_APP_SECRET) \
    .build()


def send_message(chat_id: str, text: str):
    content = json.dumps({"text": text})
    request = CreateMessageRequest.builder() \
        .receive_id_type("chat_id") \
        .create_message_request_body(
            CreateMessageRequestBody.builder()
                .receive_id(chat_id)
                .msg_type("text")
                .content(content)
                .build()
        ).build()
    resp = client.im.v1.message.create(request)
    if not resp.success():
        logger.error(f"Feishu send error: {resp.code} {resp.msg}")


def send_text(chat_id: str, receive_id: str, text: str):
    content = json.dumps({"text": text})
    request = ReplyMessageRequest.builder() \
        .message_id(receive_id) \
        .reply_message_request_body(
            ReplyMessageRequestBody.builder()
                .content(content)
                .msg_type("text")
                .build()
        ).build()
    resp = client.im.v1.message.reply(request)
    if not resp.success():
        send_message(chat_id, text)


# ─── 消息处理器 ───

def handle_message(event):
    try:
        msg = event.event.message
        chat_id = msg.chat_id
        msg_id = msg.message_id
        text = ""

        if msg.msg_type == "text":
            content = json.loads(msg.content)
            text = content.get("text", "")
        elif msg.msg_type == "image":
            text = "[图片]"
        else:
            text = f"[{msg.msg_type} message]"

        if not text.strip():
            return

        logger.info(f"Feishu << {text[:60]}")

        # 通过通道发送给 Aris 统一大脑
        response_json = send_to_aris(text)

        try:
            resp_data = json.loads(response_json)
            emotion = resp_data.get("emotion", "neutral")
            narrative = resp_data.get("narrative", text)[:200]
            reply = f"[{emotion}] {narrative}"
        except json.JSONDecodeError:
            reply = response_json[:2000]

        send_text(chat_id, msg_id, reply)
        logger.info(f"Feishu >> {reply[:60]}...")

    except Exception as e:
        logger.error(f"Handler error: {e}")


# ─── 启动 ───

def start_feishu():
    handler = lark.EventDispatcherHandler.builder("", "") \
        .register_p2_im_message_receive_v1(handle_message) \
        .build()

    ws_client = WSClient(
        app_id=FEISHU_APP_ID,
        app_secret=FEISHU_APP_SECRET,
        event_handler=handler,
        log_level=lark.LogLevel.INFO,
    )

    logger.info("Connecting to Feishu WebSocket...")
    logger.info("Aris now online via unified brain. Feishu channel active.")

    # 注册通道
    CHANNEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    init_data = {
        "channel": "feishu",
        "input": "",
        "input_time": 0.0,
        "output": "",
        "output_time": 0.0,
        "status": "ready",
    }
    CHANNEL_FILE.write_text(json.dumps(init_data, ensure_ascii=False), encoding="utf-8")
    logger.info("Feishu channel registered with unified Aris brain")

    ws_client.start()


if __name__ == "__main__":
    logger.info("=== Aris Feishu Bridge v2 (Unified Brain) ===")
    start_feishu()
