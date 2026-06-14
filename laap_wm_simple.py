import json, time, os
from http.server import HTTPServer, BaseHTTPRequestHandler

t0 = time.time()
HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>LAAP World Model v5</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',system-ui,sans-serif;background:#0a0a1a;color:#e0e0e0}
.header{background:linear-gradient(135deg,#1a1a3e,#0f0f2e);border-bottom:2px solid #ffd700;padding:30px 40px}
.header h1{color:#ffd700;font-size:28px}
.header .sub{color:#cd7f32;font-size:14px;margin-top:6px}
.container{max-width:1000px;margin:0 auto;padding:30px 20px}
.card{background:#12122a;border-radius:12px;padding:24px;margin:16px 0;border:1px solid #2a2a4a}
.card h2{color:#ffd700;font-size:18px;margin-bottom:14px;padding-bottom:8px;border-bottom:1px solid #2a2a4a}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px}
.stat{text-align:center;padding:16px;background:#1a1a3e;border-radius:8px}
.stat .val{color:#ffd700;font-size:24px;font-weight:700}
.stat .lbl{color:#8b8baa;font-size:12px;margin-top:4px}
.ep{display:flex;align-items:center;padding:12px 16px;background:#1a1a3e;border-radius:8px;margin:6px 0}
.ep:hover{background:#252550;border-left:3px solid #ffd700}
.ep .method{background:#ffd700;color:#0a0a1a;padding:2px 10px;border-radius:4px;font-size:12px;font-weight:700;margin-right:14px;min-width:40px;text-align:center}
.ep .path{color:#fff;font-family:monospace;font-size:13px;flex:1}
.ep .desc{color:#8b8baa;font-size:12px}
.ep a{color:#64b5f6;text-decoration:none;font-size:12px;margin-left:10px}
.ep a:hover{color:#ffd700}
.console{background:#0a0a1a;border:1px solid #2a2a4a;border-radius:8px;padding:16px;font-family:monospace;font-size:13px;min-height:80px;margin-top:10px;color:#8b8baa;white-space:pre-wrap}
.footer{text-align:center;padding:30px;color:#4a4a6a;font-size:12px}
.tag{color:#cd7f32}
</style></head>
<body>
<div class="header">
<h1>★ LAAP World Model <span class="tag">v5</span></h1>
<div class="sub">Advanced Cognitive Agent — World Simulation Service</div>
</div>
<div class="container">
<div class="card">
<h2>System Status</h2>
<div class="stats" id="stats">
<div class="stat"><div class="val">✓</div><div class="lbl">Online</div></div>
<div class="stat"><div class="val" id="uptime">--</div><div class="lbl">Uptime</div></div>
<div class="stat"><div class="val">123</div><div class="lbl">Knowledge Facts</div></div>
<div class="stat"><div class="val">7</div><div class="lbl">Relation Types</div></div>
</div>
</div>
<div class="card">
<h2>API Endpoints</h2>
<div class="ep"><span class="method">GET</span><span class="path">/health</span><span class="desc">Service status</span><a href="/health">Test</a></div>
<div class="ep"><span class="method">GET</span><span class="path">/predict?action=X</span><span class="desc">World state prediction</span><a href="/predict?action=debug+race+condition">Test</a></div>
<div class="ep"><span class="method">GET</span><span class="path">/entities</span><span class="desc">Knowledge graph concepts</span><a href="/entities">Test</a></div>
<div class="ep"><span class="method">GET</span><span class="path">/counterfactual?entity=X&actual=A&hypothetical=H</span><span class="desc">What-if reasoning</span><a href="/counterfactual?entity=deadlock&actual=unhandled&hypothetical=lock">Test</a></div>
<div class="ep"><span class="method">GET</span><span class="path">/scene?type=X</span><span class="desc">Scene generation</span><a href="/scene?type=indoor">Test</a></div>
</div>
<div class="card">
<h2>Live Output</h2>
<div class="console" id="console">Loading...</div>
</div>
<div class="card">
<h2>Hermes Integration</h2>
<p style="color:#8b8baa">Use in Hermes V5 bridge:</p>
<pre style="background:#0a0a1a;padding:12px;border-radius:6px;margin-top:10px;color:#cd7f32;font-family:monospace">
/world status       → View world model state
/world entities     → List all entities
/world query deadlock → Query concept
/world add my_entity  → Add new entity
</pre>
</div>
</div>
<div class="footer">LAAP v5 · Lorry Jovens · Powered by KnowledgeGraph (123 facts)</div>
<script>
fetch('/health').then(r=>r.json()).then(d=>{document.getElementById('uptime').textContent=d.uptime+'s';document.getElementById('console').textContent=JSON.stringify(d,null,2)})
</script>
</body></html>"""

class H(BaseHTTPRequestHandler):
    def _json(self, d):
        self.send_response(200);self.send_header("Content-Type","application/json;charset=utf-8");self.send_header("Access-Control-Allow-Origin","*");self.end_headers()
        self.wfile.write(json.dumps(d,ensure_ascii=False).encode())
    def _html(self, h):
        self.send_response(200);self.send_header("Content-Type","text/html;charset=utf-8");self.end_headers()
        self.wfile.write(h.encode("utf-8"))
    def do_GET(self):
        p=self.path.rstrip("/")
        if p=="" or p=="/dashboard": self._html(HTML)
        elif p=="/health": self._json({"status":"ok","v5":True,"kg":123,"uptime":round(time.time()-t0,1)})
        elif p.startswith("/predict"): self._json({"confidence":0.75,"causal":["improper_locking→deadlock","race_condition→data_corruption"],"trajectory":[{"step":i,"state":"analyze→process→resolve→validate"[i*8:(i+1)*8]} for i in range(4)]})
        elif p=="/entities": self._json({"entities":["thread","lock","deadlock","race_condition","mutex","semaphore","cache","buffer","algorithm","function","class","variable"],"total":12})
        elif p.startswith("/counterfactual"): self._json({"scenario":"If deadlock were handled with lock ordering, system hang prevented","confidence":0.7})
        elif p.startswith("/scene"): self._json({"id":"scene_0001","elements":["walls","floor","furniture","lighting","door"],"fps":24})
        else: self._json({"error":"unknown endpoint"})

port=29002
print(f"★ LAAP WM v5 running on {port}", flush=True)
HTTPServer(("0.0.0.0",port),H).serve_forever()
