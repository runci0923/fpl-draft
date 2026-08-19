#!/usr/bin/env python3
"""Helyi fogadó a böngészőből átküldött adathoz.

Miért kell: az FPL Hub és a Solio bejelentkezést kér, az fplestimator xPts-táblája
pedig anon-kulccsal zárt. Ezeknél a LAP saját kérése az egyetlen út. A böngésző
oldalán elkapjuk a választ, és ide POST-oljuk — a kulcs/token soha nem hagyja el a gépet.

Használat:  python3 tools/receiver.py <alkonyvtar>
            majd a böngészőből POST http://127.0.0.1:8793/  {"chunk":N,"players":[...]}
Kimenet:    <alkonyvtar>/chunk_NNN.json  (a merge_chunks.py fűzi össze)
"""
import http.server, json, pathlib, socketserver, sys

SUB = sys.argv[1] if len(sys.argv) > 1 else "incoming"
OUT = pathlib.Path(__file__).resolve().parent.parent / SUB
OUT.mkdir(parents=True, exist_ok=True)

class H(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "content-type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        # Chrome Private Network Access: https oldal -> http://127.0.0.1 csak ezzel megy
        self.send_header("Access-Control-Allow-Private-Network", "true")
    def do_OPTIONS(self):
        self.send_response(204); self._cors()
        self.send_header("content-length", "0"); self.end_headers()
    def do_POST(self):
        n = int(self.headers.get("content-length", 0)); body = b""
        while len(body) < n:
            c = self.rfile.read(min(65536, n - len(body)))
            if not c: break
            body += c
        try:
            d = json.loads(body)
            ch = d.get("chunk", 0)
            (OUT / f"chunk_{int(ch):03d}.json").write_text(
                json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            msg = {"ok": True, "bytes": len(body), "items": len(d.get("players", d.get("rows", [])))}
            print(f"  darab {ch}: {len(body)} bájt, {msg['items']} elem", flush=True)
        except Exception as e:
            msg = {"ok": False, "err": str(e)}; print("  HIBA:", e, flush=True)
        out = json.dumps(msg).encode()
        self.send_response(200); self._cors()
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(out))); self.end_headers()
        self.wfile.write(out)
    def log_message(self, *a): pass

class S(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True; allow_reuse_address = True

print(f"fogadó: http://127.0.0.1:8793/  ->  {OUT}", flush=True)
S(("127.0.0.1", 8793), H).serve_forever()
