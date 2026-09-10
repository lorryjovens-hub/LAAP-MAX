"""Simple HEP server on port 8765"""
import sys, os, json
sys.path.insert(0, r"D:\LAAP\harness\laap_coding\core")
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from hep_protocol import REGISTRY, HEPComponent, HEPComposer

SITE_DIR = Path(__file__).parent / "hep_site"
PORT = 8765

STYLES = [
    {"id":"cyberpunk","mode":"dark","font":"sans","c":["#0a0a0a","#1a0a0a","#00fff5","#ff00ff","#ffff00","#ff0066"]},
    {"id":"saas","mode":"light","font":"sans","c":["#ffffff","#f8fafc","#e2e8f0","#1e3a5f","#3b82f6","#64748b"]},
    {"id":"modern_dark","mode":"dark","font":"sans","c":["#0a0a0a","#1a1a2e","#16213e","#e94560","#0f3460","#ffffff"]},
    {"id":"web3","mode":"dark","font":"sans","c":["#0a0b1e","#1a1b3e","#6366f1","#8b5cf6","#06b6d4","#ffffff"]},
    {"id":"luxury","mode":"light","font":"serif","c":["#1a1a1a","#2d2d2d","#c9a84c","#f5f0e8","#8b7355","#ffffff"]},
    {"id":"terminal","mode":"dark","font":"mono","c":["#0d0d0d","#1a1a1a","#00ff41","#00cc33","#ffffff","#333333"]},
    {"id":"material","mode":"light","font":"sans","c":["#ffffff","#f5f5f5","#6200ee","#03dac6","#018786","#333333"]},
    {"id":"bauhaus","mode":"light","font":"sans","c":["#E53935","#1E88E5","#FDD835","#212121","#ffffff","#f5f0e8"]},
]

for s in STYLES:
    c = s["c"]; cid = f"style.{s['id']}"
    if not REGISTRY.get(cid):
        REGISTRY.register(HEPComponent(id=cid, name=s["id"], version="1", domain="ui", subdomain="theme",
            tags=[], inputs={}, outputs={"c":"c"}, dependencies=[],
            template=f":root{{--bg:{c[0]};--bg2:{c[1]};--bg3:{c[2]};--text:{c[3]};--text2:{c[4]};--accent:{c[5]}}}"))

class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw): super().__init__(*a, directory=str(SITE_DIR), **kw)
    def do_POST(self):
        if self.path=="/api/generate":
            d=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))).decode())
            s=next((x for x in STYLES if x["id"]==d.get("style","saas")),STYLES[0])
            c=s["c"]
            p=d.get("content","").split("\n")
            t=d.get("title","Page") or "Page"
            sec="".join(f'<section style="padding:80px 24px;background:var(--bg)"><div style="max-width:960px;margin:0 auto"><h2 style="font-size:1.8rem;margin-bottom:24px">{l[3:].strip()}</h2><div style="color:var(--text2)"><p>Body text</p></div></div></section>' for l in p if l.startswith("## "))
            h=f'<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>{t}</title><style>:root{{--bg:{c[0]};--bg2:{c[1]};--text:{c[3]};--text2:{c[4]};--accent:{c[5]}}}*{{margin:0;padding:0;box-sizing:border-box}}body{{background:var(--bg);color:var(--text);font-family:Inter,sans-serif}}.hero{{min-height:60vh;display:flex;align-items:center;justify-content:center;text-align:center;padding:0 24px;background:linear-gradient(135deg,var(--bg),var(--bg2))}}.hero h1{{font-size:clamp(2rem,5vw,3.5rem)}}</style></head><body><section class="hero"><div><h1>{t}</h1><p style="color:var(--text2)">HEP Zero-Token · {s["id"]}</p></div></section>{sec}</body></html>'
            self.send_response(200); self.send_header("Content-Type","text/html;charset=utf-8"); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(h.encode())
        else: self.send_response(404)
    def do_OPTIONS(self):
        self.send_response(200); self.send_header("Access-Control-Allow-Origin","*"); self.send_header("Access-Control-Allow-Methods","POST,GET,OPTIONS"); self.send_header("Access-Control-Allow-Headers","Content-Type"); self.end_headers()

HTTPServer(("0.0.0.0", PORT), H).serve_forever()
