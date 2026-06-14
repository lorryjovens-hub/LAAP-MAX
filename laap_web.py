"""
LAAP Digital Lifeform - Ultimate Launcher
HTTP:8081 + WS:8766 + LAAP Agent + TTS + Motion Engine
"""
import os, sys, json, time, threading, base64, subprocess
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = Path(__file__).parent / "laap" / "web" / "static"

# Character Engine
from laap.character_engine import search_character, create_character_pack, CharacterMemory
_CHARACTER_MEMORIES = {}
HTTP_PORT, WS_PORT = 8081, 8766

agent = None
_ws_clients = set()
_ws_lock = threading.Lock()
_START_TIME = time.time()

# ── TTS ──
import edge_tts
def tts_sync(text):
    result = []
    def run():
        import asyncio
        async def inner():
            audio = b""
            async for c in edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural").stream():
                if c["type"] == "audio": audio += c["data"]
            result.append(audio)
        asyncio.run(inner())
    t = threading.Thread(target=run, daemon=True); t.start(); t.join(timeout=30)
    return result[0] if result else b""

MIME = {'.vrm':'application/octet-stream','.glb':'model/gltf-binary','.html':'text/html','.js':'application/javascript','.css':'text/css','.json':'application/json'}

class H(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw): super().__init__(*a,directory=str(STATIC_DIR),**kw)
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()
    def do_GET(self):
        if self.path.startswith('/api/character/search'):
            import urllib.parse
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('q',[''])[0]
            results = search_character(q)
            self.send_response(200)
            self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            self.wfile.write(json.dumps(results).encode())
            return
        if self.path.startswith('/api/health'):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok",
                "version": "4.5.0",
                "agent": bool(agent),
                "uptime": time.time() - _START_TIME,
                "ws_clients": len(_ws_clients),
            }).encode())
            return
        if self.path.startswith('/api/agent/state'):
            self.send_response(200)
            self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            state = {"agent": bool(agent), "psi_available": False, "modules": 0}
            if agent:
                try:
                    state["psi_available"] = hasattr(agent, 'psi_driver') and agent.psi_driver is not None
                    if state["psi_available"]:
                        state["psi"] = agent.psi_driver.stats()
                    from laap.agi.core import AGIAgent
                    if isinstance(agent, AGIAgent):
                        state["modules"] = agent._module_count() if hasattr(agent, '_module_count') else 0
                except: pass
            self.wfile.write(json.dumps(state).encode())
            return
        if self.path.startswith('/api/character/load'):
            import urllib.parse
            name = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('name',[''])[0]
            pack = create_character_pack(name)
            if pack:
                mem = CharacterMemory(pack.get("character_name","default"))
                mem.init_from_pack(pack)
                _CHARACTER_MEMORIES[pack["character_name"]] = mem
                self.send_response(200)
                self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*")
                self.end_headers()
                self.wfile.write(json.dumps(pack).encode())
            else:
                self.send_response(404)
                self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*")
                self.end_headers()
                self.wfile.write(json.dumps({"error":"Character not found"}).encode())
            return
        return super().do_GET()
    def do_POST(self):
        if self.path == '/api/character/memory':
            length = int(self.headers.get('Content-Length',0))
            body = self.rfile.read(length).decode() if length else '{}'
            data = json.loads(body)
            char_name = data.get('character','default')
            content = data.get('content','')
            if char_name not in _CHARACTER_MEMORIES:
                _CHARACTER_MEMORIES[char_name] = CharacterMemory(char_name)
            _CHARACTER_MEMORIES[char_name].add_custom(content)
            self.send_response(200)
            self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            self.wfile.write(json.dumps({"status":"ok"}).encode())
            return
        self.send_response(404); self.end_headers()
        return
    def guess_type(self,p): return MIME.get(os.path.splitext(p)[1].lower()) or super().guess_type(p)
    def log_message(self,*a): pass
    def end_headers(self): self.send_header("Access-Control-Allow-Origin","*"); SimpleHTTPRequestHandler.end_headers(self)

def ws_broadcast(d):
    m = json.dumps(d, ensure_ascii=False)
    with _ws_lock:
        for ws in list(_ws_clients):
            try: ws.send(m)
            except: _ws_clients.discard(ws)

def ws_handle(ws):
    _ws_clients.add(ws)
    ws.send(json.dumps({"type":"status","status":"ready","agent":bool(agent),"tts":True}))
    try:
        for raw in ws:
            data = json.loads(raw)
            tp = data.get("type")
            if tp == "chat":
                use_psi = data.get("use_psi", False)
                domain = data.get("domain", "general")
                handle_chat(data.get("text", ""), use_psi=use_psi, domain=domain)
            elif tp == "tts":
                t = data.get("text","")
                if t.strip():
                    try:
                        a = tts_sync(t[:500])
                        ws_broadcast({"type":"tts_audio","data":base64.b64encode(a).decode(),"format":"mp3"})
                    except Exception as e:
                        ws.send(json.dumps({"type":"error","message":f"TTS: {e}"}))
    except:
        pass
    finally:
        _ws_clients.discard(ws)

def handle_chat(text, use_psi=False, domain="general"):
    ws_broadcast({"type":"user","text":text})
    if agent is None:
        ws_broadcast({"type":"response","text":"Agent unavailable"})
        return
    a = agent
    def run():
        try:
            # PSI-aware chat path
            if use_psi and hasattr(a, 'psi_driver') and a.psi_driver:
                result = a.process_interaction(text, domain=domain, use_psi=True)
                resp_text = result.get("response", "")
                ws_broadcast({"type":"response","text":resp_text})
                psi_info = result.get("psi_driver", {})
                if psi_info:
                    ws_broadcast({"type":"psi_state","data":psi_info})
                return
            
            # Legacy chat path
            from laap.ui.stream_handler import StreamHandler
            sh = StreamHandler(verbose=False, use_spinner=False)
            sh.on_token = lambda t: ws_broadcast({"type":"token","text":t})
            sh.on_tool_call = lambda n,a: ws_broadcast({"type":"tool_call","name":n})
            result = a.chat(text, handler=sh) or ""
            # Strip emoji from response text
            # Strip emoji/kaomoji
            import unicodedata
            result = "".join(c for c in result if unicodedata.category(c)[0] != "S" or c.isalnum())
            for _e in [":)","(^_^)","^^","T_T",">_<","^_^","(^^)"]: result = result.replace(_e,"")
            result = result.strip()
            ws_broadcast({"type":"response","text":result})

            try:
                es = a.lifeform.emotion_system
                n,i,cn = es.get_dominant_emotion()
                ws_broadcast({"type":"emotion","name":n,"intensity":i,"label":cn})
                v = a.lifeform.physiology.vitals
                ws_broadcast({"type":"vitals","energy":getattr(v,"energy",0.5),"focus":getattr(v,"focus",0.5),"mood":getattr(v,"mood",0.5)})
            except: pass
        except Exception as e:
            ws_broadcast({"type":"error","message":str(e)})
    threading.Thread(target=run, daemon=True).start()

ENGINE_MODE = os.environ.get("LAAP_ENGINE", "laap")  # "laap" or "hermes"

def main():
    global agent, ENGINE_MODE
    print()
    print("="*55)
    print("  LAAP Digital Lifeform - Ultimate Edition")
    print("="*55)
    print()
    # Init agent
    if ENGINE_MODE == "hermes":
        print(f"  Engine: Hermes (from env LAAP_ENGINE=hermes)")
        try:
            from laap.hermes_bridge import HermesAgentWrapper
            agent = HermesAgentWrapper()
            print(f"  Agent: {agent.name} ✅")
        except Exception as e:
            print(f"  Hermes init failed: {e}")
            print("  Falling back to LAAP engine")
            ENGINE_MODE = "laap"
    
    if ENGINE_MODE == "laap":
        print("[1/4] Initializing LAAP Agent...")
        try:
            from laap.cli.config_manager import config_manager
            config_manager.apply_to_environment()
            from laap.llm.factory import LLMFactory
            from laap.agent.lifelike import LifelikeConfig
            from laap.lifeform import LifeformAgent
            factory = LLMFactory(default_provider="deepseek", default_model="deepseek-v4-flash")
            agent = LifeformAgent(config=LifelikeConfig(name="Ao", verbose=False), llm_factory=factory, show_banner=False)
            print(f"  Agent: {agent.config.name} ✅")
        except Exception as e:
            print(f"  Agent: {e} (model mode)")
        # Start HTTP
    print("[2/4] Starting HTTP server...")
    httpd = HTTPServer(("0.0.0.0", HTTP_PORT), H)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    # Start WS
    print("[3/4] Starting WebSocket server...")
    import websockets.sync.server
    def sws():
        with websockets.sync.server.serve(ws_handle, "0.0.0.0", WS_PORT) as s:
            s.serve_forever()
    threading.Thread(target=sws, daemon=True).start()
    # Ready
    print("[4/4] Ready!")
    print()
    print(f"  🌐 http://localhost:{HTTP_PORT}")
    print(f"  🔌 ws://localhost:{WS_PORT}")
    print(f"  🤖 Agent: {'ON' if agent else 'OFF'}  🔊 TTS: ON  🎭 Motion: 15 presets")
    print()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("Stopped")

if __name__ == "__main__":
    main()
