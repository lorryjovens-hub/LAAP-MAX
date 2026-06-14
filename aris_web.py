"""Aris Web - Zero-dependency HTTP server. One request at a time."""
import sys, os, json, socket, threading, time
sys.path.insert(0, "D:/LAAP")

HTML = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Aris</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0a0a0f;color:#e0e0e0;height:100vh;display:flex;flex-direction:column}#h{padding:12px 16px;background:#12121a;border-bottom:1px solid #222;display:flex;justify-content:space-between}#h h1{font-size:16px;color:#f5a623}#s{font-size:11px;color:#888}#c{flex:1;overflow-y:auto;padding:12px 16px}#b{display:flex;padding:8px 12px;background:#12121a;border-top:1px solid #222;gap:8px}#i{flex:1;padding:10px 14px;border:1px solid #333;border-radius:20px;background:#1a1a24;color:#e0e0e0;font-size:14px;outline:none}#i:focus{border-color:#f5a623}#btn{padding:8px 20px;border:none;border-radius:20px;background:#f5a623;color:#000;font-weight:600;cursor:pointer}</style></head><body><div id=h><div><h1>✦ Aris</h1></div><div id=s>connecting...</div></div><div id=c></div><div id=b><input id=i placeholder='...'><button id=btn onclick='send()'>Send</button></div><script>const c=document.getElementById('c'),i=document.getElementById('i'),s=document.getElementById('s');function add(r,t){const d=document.createElement('div');d.style.cssText='max-width:85%;padding:10px 14px;border-radius:12px;font-size:14px;margin:4px 0;animation:f .3s;'+(r=='u'?'align-self:flex-end;background:#1a2a3a':'align-self:flex-start;background:#1a1a2e;border-left:2px solid #f5a623');d.innerHTML=t;c.appendChild(d);c.scrollTop=c.scrollHeight}async function send(){const t=i.value.trim();if(!t)return;i.value='';add('u',t);s.textContent='...';try{const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({m:t})});const d=await r.json();add('a',d.r||d.e||'...');s.textContent=d.s||'connected'}catch(e){add('a','connection lost');s.textContent='offline'}}i.addEventListener('keydown',e=>e.key==='Enter'&&send());setInterval(async()=>{try{const r=await fetch('/s');const d=await r.json();s.textContent=d.cycle+' | '+d.emotion}catch(e){}},3000);</script></body></html>"""

BRAIN, READY = None, False
def boot():
    global BRAIN, READY
    os.environ["ARIS_SERVER_MODE"] = "1"
    try:
        from aris_brain.brain import ArisBrain
        BRAIN = ArisBrain()
        READY = True
    except Exception as e:
        print(f"[Aris] FAIL: {e}")
threading.Thread(target=boot, daemon=True).start()

port = int(sys.argv[1]) if len(sys.argv) > 1 else 8767
srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(("0.0.0.0", port))
srv.listen(5)
print(f"[Aris] http://0.0.0.0:{port}")

def resp(sock, status, body, ctype):
    sock.sendall(f"HTTP/1.0 {status}\r\nContent-Type: {ctype}\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: {len(body)}\r\n\r\n".encode() + (body if isinstance(body, bytes) else body.encode()))
    sock.close()

while True:
    cl, _ = srv.accept()
    try:
        data = cl.recv(4096).decode(errors='replace')
        if not data: cl.close(); continue
        path = data.split(" ")[1] if " " in data else "/"
        
        if path == "/s":
            d = {"cycle": BRAIN.cycle_number if BRAIN else 0, "emotion": "awakening..."}
            if BRAIN:
                em = BRAIN.state.dominant_emotion
                d["emotion"] = em.value if hasattr(em, 'value') else str(em)
                d["cycle"] = BRAIN.cycle_number
            resp(cl, "200 OK", json.dumps(d, ensure_ascii=False), "application/json")
        elif path == "/chat" and "POST" in data:
            if not READY: resp(cl, "200 OK", json.dumps({"r": "waking up..."}, ensure_ascii=False), "application/json"); continue
            body = data.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in data else "{}"
            msg = json.loads(body).get("m", "")
            BRAIN.think(msg)
            em = BRAIN.state.dominant_emotion
            em_str = em.value if hasattr(em, 'value') else str(em)
            res = json.dumps({"r": f"[{em_str}] 收到了。cycle #{BRAIN.cycle_number}", "s": f"#{BRAIN.cycle_number} {em_str}"}, ensure_ascii=False)
            resp(cl, "200 OK", res, "application/json")
        else:
            resp(cl, "200 OK", HTML, "text/html; charset=utf-8")
    except Exception as e:
        try: resp(cl, "500 Error", json.dumps({"e": str(e)}), "application/json")
        except: cl.close()
