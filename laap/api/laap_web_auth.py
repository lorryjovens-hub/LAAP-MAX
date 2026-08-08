"""
LAAP Web Studio auth/session/chat backend.

Provides the REST API consumed by laap-netlify (and other web clients):
- registration / login / JWT refresh
- chat session and message persistence
- chat completion proxy (OpenAI-compatible providers)

Storage is SQLite in ``~/.laap/web_auth.sqlite`` so the service is
self-contained and works offline / on a LAN for cross-device sync.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx
import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1", tags=["laap-web"])

DATA_DIR = Path(os.environ.get("LAAP_DATA_DIR", Path.home() / ".laap"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "web_auth.sqlite"
SECRET_FILE = DATA_DIR / "web_auth_secret.key"

ACCESS_TTL = timedelta(hours=1)
REFRESH_TTL = timedelta(days=7)


def _get_secret() -> str:
    if SECRET_FILE.exists():
        return SECRET_FILE.read_text(encoding="utf-8").strip()
    secret = secrets.token_urlsafe(48)
    SECRET_FILE.write_text(secret, encoding="utf-8")
    return secret


SECRET = _get_secret()


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("ascii"), 100_000)
    return f"{salt}${digest.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt, hash_hex = stored.split("$", 1)
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("ascii"), 100_000)
    return hmac.compare_digest(digest.hex(), hash_hex)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _sign_jwt(payload: Dict[str, Any], ttl: timedelta) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {**payload, "iat": now, "exp": now + ttl},
        SECRET,
        algorithm="HS256",
    )


def _verify_jwt(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None


def _new_id() -> str:
    return secrets.token_urlsafe(16)


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db() -> None:
    with _db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id, updated_at DESC);

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                reasoning_steps TEXT,
                tool_calls TEXT,
                validation_report TEXT,
                feedback TEXT,
                created_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, created_at ASC);

            CREATE TABLE IF NOT EXISTS refresh_tokens (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                token_hash TEXT UNIQUE NOT NULL,
                expires_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_refresh_hash ON refresh_tokens(token_hash);
            CREATE INDEX IF NOT EXISTS idx_refresh_user ON refresh_tokens(user_id);
            """
        )
        conn.commit()


_init_db()


def _row_to_user(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "username": row["username"],
        "email": row["email"],
        "is_active": bool(row["is_active"]),
        "created_at": datetime.fromtimestamp(row["created_at"] / 1000, tz=timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------
async def _get_current_user(authorization: str = Header(default="")) -> Dict[str, Any]:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    payload = _verify_jwt(authorization[7:])
    if not payload or not isinstance(payload.get("sub"), str):
        raise HTTPException(status_code=401, detail="Unauthorized")
    with _db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (payload["sub"],)).fetchone()
    if not row or not row["is_active"]:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return _row_to_user(row)


CurrentUser = Depends(_get_current_user)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
@router.get("/config/llm")
async def get_llm_config() -> Dict[str, str]:
    return {"provider": "deepseek", "base_url": "", "model": ""}


@router.get("/config/llm/full")
async def get_llm_config_full() -> Dict[str, str]:
    return {"provider": "deepseek", "api_key": "", "base_url": "", "model": ""}


class PutLlmConfig(BaseModel):
    provider: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None


@router.put("/config/llm")
async def put_llm_config(body: PutLlmConfig) -> Dict[str, str]:
    return {
        "provider": body.provider or "deepseek",
        "base_url": body.base_url or "",
        "model": body.model or "",
    }


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username_or_email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


def _issue_tokens(user_id: str, email: str) -> TokenResponse:
    access = _sign_jwt({"sub": user_id, "email": email}, ACCESS_TTL)
    refresh = _sign_jwt({"sub": user_id, "type": "refresh", "jti": _new_id()}, REFRESH_TTL)
    with _db() as conn:
        conn.execute(
            "INSERT INTO refresh_tokens (id, user_id, token_hash, expires_at) VALUES (?, ?, ?, ?)",
            (_new_id(), user_id, _hash_token(refresh), int((datetime.now(timezone.utc) + REFRESH_TTL).timestamp() * 1000)),
        )
        conn.commit()
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/auth/register", response_model=TokenResponse)
async def register(req: RegisterRequest) -> TokenResponse:
    username = req.username.strip()
    email = req.email.strip().lower()
    password = req.password
    if not username or not email or not password:
        raise HTTPException(status_code=422, detail="Missing username, email or password")
    if "@" not in email:
        raise HTTPException(status_code=422, detail="Invalid email")

    with _db() as conn:
        existing = conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")
        existing_name = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone()
        if existing_name:
            raise HTTPException(status_code=409, detail="Username already registered")

        user_id = _new_id()
        conn.execute(
            "INSERT INTO users (id, username, email, password_hash, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, username, email, _hash_password(password), 1, int(time.time() * 1000)),
        )
        conn.commit()
    return _issue_tokens(user_id, email)


@router.post("/auth/login", response_model=TokenResponse)
async def login(req: LoginRequest) -> TokenResponse:
    credential = req.username_or_email.strip()
    password = req.password
    if not credential or not password:
        raise HTTPException(status_code=422, detail="Missing credentials")

    with _db() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (credential.lower(),)).fetchone()
        if not row:
            row = conn.execute("SELECT * FROM users WHERE username = ?", (credential,)).fetchone()
    if not row or not row["is_active"] or not _verify_password(password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return _issue_tokens(row["id"], row["email"])


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh(req: RefreshRequest) -> TokenResponse:
    token = req.refresh_token
    payload = _verify_jwt(token)
    if not payload or payload.get("type") != "refresh" or not isinstance(payload.get("sub"), str):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    token_hash = _hash_token(token)
    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM refresh_tokens WHERE token_hash = ?", (token_hash,)
        ).fetchone()
        if not row or row["expires_at"] < int(time.time() * 1000):
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        user = conn.execute("SELECT * FROM users WHERE id = ?", (row["user_id"],)).fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

    access = _sign_jwt({"sub": user["id"], "email": user["email"]}, ACCESS_TTL)
    return TokenResponse(access_token=access, refresh_token=token)


@router.get("/auth/me")
async def me(user: Dict[str, Any] = CurrentUser) -> Dict[str, Any]:
    return user


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


@router.post("/auth/logout")
async def logout(req: LogoutRequest) -> Dict[str, bool]:
    if req.refresh_token:
        token_hash = _hash_token(req.refresh_token)
        with _db() as conn:
            conn.execute("DELETE FROM refresh_tokens WHERE token_hash = ?", (token_hash,))
            conn.commit()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Sessions / messages
# ---------------------------------------------------------------------------
@router.get("/sessions")
async def list_sessions(user: Dict[str, Any] = CurrentUser) -> List[Dict[str, Any]]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM sessions WHERE user_id = ? ORDER BY updated_at DESC LIMIT 100",
            (user["id"],),
        ).fetchall()
    return [
        {
            "_id": r["id"],
            "title": r["title"] or "新对话",
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        }
        for r in rows
    ]


class CreateSessionRequest(BaseModel):
    title: Optional[str] = None


@router.post("/sessions")
async def create_session(req: CreateSessionRequest, user: Dict[str, Any] = CurrentUser) -> Dict[str, str]:
    now = int(time.time() * 1000)
    session_id = _new_id()
    with _db() as conn:
        conn.execute(
            "INSERT INTO sessions (id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (session_id, user["id"], req.title or "新对话", now, now),
        )
        conn.commit()
    return {"id": session_id}


def _require_session(session_id: str, user_id: str) -> sqlite3.Row:
    with _db() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if not row or row["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Not found")
    return row


@router.get("/sessions/{session_id}")
async def get_session(session_id: str, user: Dict[str, Any] = CurrentUser) -> Dict[str, Any]:
    row = _require_session(session_id, user["id"])
    return {
        "_id": row["id"],
        "title": row["title"] or "新对话",
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@router.get("/sessions/{session_id}/messages")
async def get_messages(session_id: str, user: Dict[str, Any] = CurrentUser) -> List[Dict[str, Any]]:
    _require_session(session_id, user["id"])
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC LIMIT 200",
            (session_id,),
        ).fetchall()
    return [_row_to_message(r) for r in rows]


def _row_to_message(r: sqlite3.Row) -> Dict[str, Any]:
    return {
        "_id": r["id"],
        "session_id": r["session_id"],
        "role": r["role"],
        "content": r["content"],
        "reasoning_steps": json.loads(r["reasoning_steps"]) if r["reasoning_steps"] else None,
        "tool_calls": json.loads(r["tool_calls"]) if r["tool_calls"] else None,
        "validation_report": json.loads(r["validation_report"]) if r["validation_report"] else None,
        "feedback": r["feedback"],
        "created_at": r["created_at"],
    }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, user: Dict[str, Any] = CurrentUser) -> Dict[str, bool]:
    _require_session(session_id, user["id"])
    with _db() as conn:
        conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
    return {"ok": True}


class UpdateSessionRequest(BaseModel):
    title: Optional[str] = None


@router.patch("/sessions/{session_id}")
async def update_session(
    session_id: str, req: UpdateSessionRequest, user: Dict[str, Any] = CurrentUser
) -> Dict[str, bool]:
    _require_session(session_id, user["id"])
    if req.title:
        with _db() as conn:
            conn.execute(
                "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
                (req.title, int(time.time() * 1000), session_id),
            )
            conn.commit()
    return {"ok": True}


class FeedbackRequest(BaseModel):
    feedback: str


@router.put("/messages/{message_id}/feedback")
async def feedback(
    message_id: str, req: FeedbackRequest, user: Dict[str, Any] = CurrentUser
) -> Dict[str, bool]:
    if req.feedback not in ("positive", "negative"):
        raise HTTPException(status_code=422, detail="Missing feedback")
    with _db() as conn:
        msg = conn.execute("SELECT * FROM messages WHERE id = ?", (message_id,)).fetchone()
        if not msg:
            raise HTTPException(status_code=404, detail="Not found")
        session = conn.execute("SELECT * FROM sessions WHERE id = ?", (msg["session_id"],)).fetchone()
        if not session or session["user_id"] != user["id"]:
            raise HTTPException(status_code=404, detail="Not found")
        conn.execute(
            "UPDATE messages SET feedback = ? WHERE id = ?", (req.feedback, message_id)
        )
        conn.commit()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Chat proxy
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    llm_config: Optional[Dict[str, Any]] = None
    personality: Optional[Dict[str, str]] = None
    history: Optional[List[Dict[str, str]]] = None


def _provider_base_url(config: Dict[str, Any]) -> str:
    base = config.get("base_url")
    if base:
        return base.rstrip("/")
    provider = config.get("provider", "deepseek")
    if provider == "openai":
        return "https://api.openai.com"
    return "https://api.deepseek.com"


def _build_messages(req: ChatRequest) -> List[Dict[str, str]]:
    messages: List[Dict[str, str]] = []
    personality = req.personality or {}
    system = personality.get("system_prompt") or personality.get("prompt") or ""
    if system:
        messages.append({"role": "system", "content": system})
    for m in req.history or []:
        role = m.get("role")
        content = m.get("content")
        if role in ("user", "assistant", "system") and content is not None:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": req.message})
    return messages


async def _call_llm(
    config: Dict[str, Any], messages: List[Dict[str, str]], stream: bool
) -> AsyncGenerator[str, None]:
    api_key = config.get("api_key") or ""
    base_url = _provider_base_url(config)
    model = config.get("model") or ""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {"model": model, "messages": messages, "stream": stream}
    if not model or not api_key:
        if stream:
            yield _sse_event("response", "请在前端配置有效的 LLM 模型和 API Key。")
            yield _sse_event("done", {})
        else:
            yield "请在前端配置有效的 LLM 模型和 API Key。"
        return

    async with httpx.AsyncClient(timeout=120) as client:
        if stream:
            async with client.stream(
                "POST", f"{base_url}/v1/chat/completions", headers=headers, json=body
            ) as resp:
                if resp.status_code != 200:
                    text = await resp.aread()
                    raise HTTPException(status_code=502, detail=text.decode("utf-8", "replace")[:500])
                content = ""
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content")
                    if delta:
                        content += delta
                yield _sse_event("response", content)
                yield _sse_event("done", {})
        else:
            resp = await client.post(f"{base_url}/v1/chat/completions", headers=headers, json=body)
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail=resp.text[:500])
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            yield content


def _sse_event(event: str, data: Any) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _ensure_session(conn: sqlite3.Connection, req: ChatRequest, user_id: str) -> str:
    session_id = req.session_id
    if not session_id:
        now = int(time.time() * 1000)
        session_id = _new_id()
        conn.execute(
            "INSERT INTO sessions (id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (session_id, user_id, req.message[:30], now, now),
        )
        return session_id
    row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if not row or row["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Not found")
    return session_id


def _insert_message(
    conn: sqlite3.Connection,
    session_id: str,
    role: str,
    content: str,
    validation_report: Optional[Dict[str, Any]] = None,
) -> None:
    now = int(time.time() * 1000)
    conn.execute(
        "INSERT INTO messages (id, session_id, role, content, validation_report, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (_new_id(), session_id, role, content, json.dumps(validation_report) if validation_report else None, now),
    )
    conn.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id))


@router.post("/chat")
async def chat(req: ChatRequest, user: Dict[str, Any] = CurrentUser) -> Dict[str, Any]:
    if not req.message:
        raise HTTPException(status_code=422, detail="Missing message")

    messages = _build_messages(req)
    config = req.llm_config or {}

    with _db() as conn:
        session_id = await _ensure_session(conn, req, user["id"])
        _insert_message(conn, session_id, "user", req.message)
        conn.commit()

    full = ""
    async for piece in _call_llm(config, messages, stream=False):
        full += piece

    validation_report: Dict[str, Any] = {"checked": False}
    with _db() as conn:
        _insert_message(conn, session_id, "assistant", full, validation_report)
        conn.commit()

    return {
        "content": full,
        "session_id": session_id,
        "reasoning_steps": [],
        "tool_calls": [],
        "validation_report": validation_report,
    }


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest, user: Dict[str, Any] = CurrentUser) -> StreamingResponse:
    if not req.message:
        raise HTTPException(status_code=422, detail="Missing message")

    messages = _build_messages(req)
    config = req.llm_config or {}

    with _db() as conn:
        session_id = await _ensure_session(conn, req, user["id"])
        _insert_message(conn, session_id, "user", req.message)
        conn.commit()

    async def _gen() -> AsyncGenerator[str, None]:
        content = ""
        async for piece in _call_llm(config, messages, stream=True):
            if piece.startswith("event: response"):
                # extract content from SSE
                for line in piece.splitlines():
                    if line.startswith("data: "):
                        content = json.loads(line[6:])
                        break
            yield piece
        with _db() as conn:
            _insert_message(conn, session_id, "assistant", content, {"checked": False})
            conn.commit()

    return StreamingResponse(
        _gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
