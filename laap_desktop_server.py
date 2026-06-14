"""
LAAP Desktop Server — Lightweight startup (HTTP:8081 + WS:8766)
Bypasses heavy LAAP agent init for faster startup.
Agent loads on first chat request.
"""
import os, sys, json, time, threading, base64
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = Path(__file__).parent / "laap" / "web" / "static"
HTTP_PORT, WS_PORT = 8081, 8766

agent = None
agent_lock = threading.Lock()
_ws_clients = set()
_ws_lock = threading.Lock()
_START_TIME = time.time()

MIME = {'.vrm':'application/octet-stream','.glb':'model/gltf-binary','.html':'text/html',
        '.js':'application/javascript','.css':'text/css','.json':'application/json'}

def lazy_init_agent():
    """Load LAAP agent on first use."""
    global agent
    with agent_lock:
        if agent is not None:
            return agent
        try:
            from laap.lifeform import LifeformAgent
            from laap.agent.lifelike import LifelikeConfig
            from laap.llm.factory import LLMFactory
            factory = LLMFactory(default_provider="deepseek", default_model="deepseek-v4-flash")
            agent = LifeformAgent(
                config=LifelikeConfig(name="Ao", verbose=False),
                llm_factory=factory,
                show_banner=False,
            )
        except Exception as e:
            print(f"[LAAP] Agent init deferred: {e}")
            # Still need a minimal agent for status
            agent = type("Minimal", (), {"__bool__": lambda s: False})()
        return agent

class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(STATIC_DIR), **kw)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def do_GET(self):
        import urllib.parse
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        # CORS headers for all responses
        def send_json(data, status=200):
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

        # Health check
        if self.path == "/api/health" or self.path.startswith("/api/health"):
            send_json({
                "status": "ok",
                "version": "4.5.0",
                "agent": agent is not None and bool(agent),
                "uptime": time.time() - _START_TIME,
                "ws_clients": len(_ws_clients),
                "mode": "desktop",
            })
            return

        # Agent state
        if self.path.startswith("/api/agent/state"):
            state = {
                "agent": agent is not None and bool(agent),
                "psi_available": False,
                "modules": 0,
                "uptime": time.time() - _START_TIME,
            }
            if agent and hasattr(agent, "psi_driver") and agent.psi_driver:
                state["psi_available"] = True
                state["psi"] = agent.psi_driver.stats()
            send_json(state)
            return

        # Character search
        if self.path.startswith("/api/character/search"):
            q = params.get("q", [""])[0]
            try:
                from laap.character_engine import search_character
                results = search_character(q)
            except ImportError:
                results = []
            send_json(results)
            return

        # Character load
        if self.path.startswith("/api/character/load"):
            name = params.get("name", [""])[0]
            try:
                from laap.character_engine import create_character_pack
                pack = create_character_pack(name)
                if pack:
                    send_json(pack)
                else:
                    send_json({"error": "Character not found"}, 404)
            except ImportError:
                send_json({"error": "Character engine unavailable"}, 503)
            return

        # Default: serve static files
        return super().do_GET()

    def do_POST(self):
        # CORS
        self.send_header("Access-Control-Allow-Origin", "*")

        import urllib.parse
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode() if length else "{}"
        data = json.loads(body) if body else {}

        def send_json(resp, status=200):
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(resp, ensure_ascii=False).encode())

        if self.path == "/api/chat":
            text = data.get("text", "")
            domain = data.get("domain", "general")
            use_psi = data.get("use_psi", False)
            # Trigger agent init
            lazy_init_agent()
            send_json({"status": "queued", "via": "ws"})
            return

        send_json({"error": "not_found"}, 404)

    def guess_type(self, p):
        return MIME.get(os.path.splitext(p)[1].lower()) or super().guess_type(p)

    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()


# ── WebSocket Handler ──

def ws_broadcast(d):
    m = json.dumps(d, ensure_ascii=False)
    with _ws_lock:
        for ws in list(_ws_clients):
            try:
                ws.send(m)
            except:
                _ws_clients.discard(ws)

def ws_handle(ws):
    _ws_clients.add(ws)
    ws.send(json.dumps({
        "type": "status",
        "status": "ready",
        "agent": agent is not None and bool(agent),
    }))
    try:
        for raw in ws:
            data = json.loads(raw)
            tp = data.get("type")
            if tp == "chat":
                text = data.get("text", "")
                domain = data.get("domain", "general")
                use_psi = data.get("use_psi", False)
                a = lazy_init_agent()
                # Stream tokens via broadcast
                ws_broadcast({"type": "token", "text": f"[Thinking about: {text[:50]}...]\n"})
                if a and bool(a):
                    try:
                        result = a.chat(text) or ""
                        ws_broadcast({"type": "response", "text": result})
                        # Emit fake emotion/vitals for demo
                        ws_broadcast({"type": "emotion", "name": "curious", "intensity": 0.7, "label": "好奇"})
                        ws_broadcast({"type": "vitals", "energy": 0.8, "focus": 0.9, "mood": 0.7})
                    except Exception as e:
                        ws_broadcast({"type": "error", "message": str(e)})
                else:
                    ws_broadcast({"type": "response", "text": f"Agent initializing... Please try again in a moment.\n\nYou said: {text}"})
            elif tp == "status":
                ws.send(json.dumps({
                    "type": "status", "status": "ready",
                    "agent": agent is not None and bool(agent),
                }))
    except:
        pass
    finally:
        _ws_clients.discard(ws)


def main():
    print()
    print("=" * 55)
    print("  LAAP Desktop Server")
    print("=" * 55)
    print()

    # HTTP server
    print(f"[1/2] Starting HTTP on :{HTTP_PORT}...")
    httpd = HTTPServer(("127.0.0.1", HTTP_PORT), H)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    # WebSocket server
    print(f"[2/2] Starting WebSocket on :{WS_PORT}...")
    try:
        import websockets.sync.server
        def sws():
            with websockets.sync.server.serve(ws_handle, "127.0.0.1", WS_PORT) as s:
                s.serve_forever()
        threading.Thread(target=sws, daemon=True).start()
    except ImportError:
        print("  ⚠ websockets not installed — WS unavailable")
        print("  Install: pip install websockets")

    print()
    print(f"  🌐 http://localhost:{HTTP_PORT}")
    print(f"  🔌 ws://localhost:{WS_PORT}")
    print(f"  🤖 Agent: lazy-init (loads on first chat)")
    print()
    print("  Press Ctrl+C to stop")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
