"""Standalone HEP static server only"""
import os, json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

SITE_DIR = Path(os.path.dirname(__file__)) / "hep_site"
PORT = 8765

class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(SITE_DIR), **kw)
    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b'{"status":"ok","message":"HEP server running"}')
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

print(f"LAAP HEP at http://localhost:{PORT}")
HTTPServer(("0.0.0.0", PORT), H).serve_forever()
