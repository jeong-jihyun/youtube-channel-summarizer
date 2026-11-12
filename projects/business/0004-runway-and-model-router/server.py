"""표준 웹 서버 (표준 라이브러리만 사용).
  python3 server.py            -> http://localhost:8000  (PORT 환경변수로 포트 변경)
  GET /            화면(버튼으로 실행)   GET /api/run?키=값   JSON 결과   GET /health   상태 확인"""
import importlib
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
CFG = json.load(open(os.path.join(HERE, "project.json"), encoding="utf-8"))
_mod, _fn = CFG["entry"].split(":")
API = getattr(importlib.import_module(_mod), _fn)

PAGE = """<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>body{font:16px/1.55 sans-serif;max-width:720px;margin:0 auto;padding:16px}label{display:block;margin:12px 0 4px;color:#555;font-size:.9rem}
input,textarea{width:100%;font:inherit;padding:12px;border:1px solid #ccc;border-radius:10px;box-sizing:border-box}textarea{min-height:100px}
button{font:inherit;font-weight:700;min-height:48px;padding:0 20px;border:0;border-radius:12px;background:#2563eb;color:#fff;margin-top:14px}
pre{background:#f3f4f6;padding:12px;border-radius:10px;overflow:auto;white-space:pre-wrap;word-break:break-word;font-size:.85rem}img{max-width:100%}</style>
<h1>__TITLE__</h1><div id="f">__FIELDS__</div><button onclick="run()">실행</button> <span id="s"></span><div id="img"></div><pre id="out">(아직 실행 안 함)</pre>
<script>
async function run(){const q=new URLSearchParams();document.querySelectorAll('[data-k]').forEach(e=>q.set(e.dataset.k,e.value));
 document.getElementById('s').textContent='실행 중...';
 try{const r=await fetch('/api/run?'+q);const j=await r.json();document.getElementById('s').textContent=j.ok?'성공':'실패';
 if(j.gif_base64){document.getElementById('img').innerHTML='<img src="data:image/gif;base64,'+j.gif_base64+'">';j.gif_base64='(그림 데이터 생략)';}
 if(j.ics){j.ics='('+j.ics_lines+'줄)';}
 document.getElementById('out').textContent=j.text||JSON.stringify(j,null,2);}catch(e){document.getElementById('s').textContent='오류: '+e}}
</script>"""


def fields_html():
    import html
    out = []
    for i in CFG.get("inputs", []):
        k, v = html.escape(i["key"]), html.escape(str(i.get("default", "")))
        out.append("<label>%s</label>" % html.escape(i["label"]))
        if i.get("type") == "textarea":
            out.append('<textarea data-k="%s">%s</textarea>' % (k, v))
        else:
            out.append('<input data-k="%s" type="%s" value="%s">' % (k, {"date": "date", "number": "number"}.get(i.get("type"), "text"), v))
    return "".join(out)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/":
            self._send(200, PAGE.replace("__TITLE__", CFG["title"]).replace("__FIELDS__", fields_html()), "text/html")
        elif u.path == "/health":
            self._send(200, json.dumps({"ok": True, "name": CFG["name"]}), "application/json")
        elif u.path == "/api/run":
            params = {k: v[0] for k, v in parse_qs(u.query).items()}
            try:
                self._send(200, json.dumps(API(params), ensure_ascii=False), "application/json")
            except Exception as e:  # 입력이 잘못된 경우 등
                self._send(400, json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False), "application/json")
        else:
            self._send(404, json.dumps({"ok": False, "error": "not found"}), "application/json")

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print(f"{CFG['title']} 실행 중: http://localhost:{port}")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
