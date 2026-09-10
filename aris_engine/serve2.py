"""HEP server on port 8767"""
import sys, json
sys.path.insert(0, r"D:\LAAP\harness\laap_coding\core")
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from hep_protocol import REGISTRY, HEPComponent

SITE_DIR = Path(__file__).parent / "hep_site"
PORT = 8767

STYLES = [
    {"id":"cyberpunk","c":["#0a0a0a","#1a0a0a","#00fff5","#ff00ff","#ffff00","#ff0066"]},
    {"id":"saas","c":["#ffffff","#f8fafc","#e2e8f0","#1e3a5f","#3b82f6","#64748b"]},
    {"id":"modern_dark","c":["#0a0a0a","#1a1a2e","#16213e","#e94560","#0f3460","#ffffff"]},
]
for s in STYLES:
    c=s["c"]
    if not REGISTRY.get(f"style.{s['id']}"):
        REGISTRY.register(HEPComponent(id=f"style.{s['id']}",name=s["id"],version="1",domain="ui",subdomain="theme",tags=[],inputs={},outputs={"c":"c"},dependencies=[],template=f":root{{--bg:{c[0]};--bg2:{c[1]};--bg3:{c[2]};--text:{c[3]};--text2:{c[4]};--accent:{c[5]}}}"))

class H(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw): super().__init__(*a,directory=str(SITE_DIR),**kw)
    def do_POST(self):
        if self.path=="/api/generate":
            d=json.loads(self.rfile.read(int(self.headers["Content-Length"])).decode())
            s=next((x for x in STYLES if x["id"]==d.get("style","saas")),STYLES[1])
            c=s["c"]; t=d.get("title","P")
            h=f'<!DOCTYPE html><html><head><meta charset="UTF-8"><title>{t}</title><style>:root{{--bg:{c[0]};--bg2:{c[1]};--text:{c[3]};--accent:{c[5]}}}*{{margin:0;padding:0}}body{{background:var(--bg);color:var(--text);font-family:Inter,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh}}.hero{{text-align:center}}.hero h1{{font-size:3rem;margin-bottom:16px;color:var(--text)}}</style></head><body><div class="hero"><h1>{t}</h1><p style="color:var(--text2)">HEP · {s["id"]}</p></div></body></html>'
            self.send_response(200);self.send_header("Content-Type","text/html;charset=utf-8");self.send_header("Access-Control-Allow-Origin","*");self.end_headers();self.wfile.write(h.encode())
        else:self.send_response(404)
    def do_OPTIONS(self):
        self.send_response(200);self.send_header("Access-Control-Allow-Origin","*");self.send_header("Access-Control-Allow-Methods","POST,GET,OPTIONS");self.send_header("Access-Control-Allow-Headers","Content-Type");self.end_headers()

print(f"HEP server on :{PORT}")
HTTPServer(("0.0.0.0",PORT),H).serve_forever()
