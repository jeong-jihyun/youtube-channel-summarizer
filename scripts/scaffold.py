"""프로젝트 표준 파일 생성기.
사용법:  python3 scripts/scaffold.py projects/<분류>/<번호-이름>
프로젝트 폴더에 project.json 이 있어야 한다:
  {"name": "...", "title": "...", "entry": "모듈:함수", "script": "실행 스크립트.py", "requirements": ["패키지"]}
entry 함수는 api(params: dict) -> dict 형태이며, 결과에 "ok": True/False 가 들어 있어야 한다.
만들어지는 파일: server.py(웹 서버+JSON API), test_project.py(자동 시험), Makefile, Dockerfile, requirements.txt, .dockerignore"""
import json
import os
import sys

SERVER = '''"""표준 웹 서버 (표준 라이브러리만 사용).
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
 document.getElementById('out').textContent=JSON.stringify(j,null,2);}catch(e){document.getElementById('s').textContent='오류: '+e}}
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
'''

TEST = '''"""표준 시험: (1) 스크립트가 직접 실행되어 '성공'을 출력하는지 (2) 웹 서버와 JSON API가 동작하는지."""
import json
import os
import subprocess
import sys
import threading
import unittest
import urllib.request
from http.server import HTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
CFG = json.load(open(os.path.join(HERE, "project.json"), encoding="utf-8"))


class ProjectTest(unittest.TestCase):
    def test_script_runs(self):
        r = subprocess.run([sys.executable, CFG["script"]], cwd=HERE, capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("성공", r.stdout)

    def test_api_function(self):
        import importlib
        mod, fn = CFG["entry"].split(":")
        result = getattr(importlib.import_module(mod), fn)({})
        self.assertTrue(result.get("ok"), result)

    def test_http(self):
        import server
        httpd = HTTPServer(("127.0.0.1", 0), server.Handler)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{httpd.server_port}"
        try:
            self.assertTrue(json.load(urllib.request.urlopen(base + "/health"))["ok"])
            self.assertTrue(json.load(urllib.request.urlopen(base + "/api/run"))["ok"])
            self.assertIn("<button", urllib.request.urlopen(base + "/").read().decode("utf-8"))
        finally:
            httpd.shutdown()


if __name__ == "__main__":
    unittest.main()
'''

MAKEFILE = '''# 사용법: make test(시험)  make run(실행)  make docker(컨테이너로 실행)
test:
\tpython3 -m unittest -v test_project

run:
\tpython3 server.py

install:
\tpip install -r requirements.txt

docker:
\tdocker build -t {name} .
\tdocker run --rm -p 8000:8000 {name}
'''

DOCKERFILE = '''FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=8000
EXPOSE 8000
CMD ["python", "server.py"]
'''


LAB_URL = "https://jeong-jihyun.github.io/lab/"
BEGIN, END_ = "<!-- standard:begin -->", "<!-- standard:end -->"


def readme_block(cfg):
    uses = "\n".join("- " + u for u in cfg.get("uses", [])) or "- (활용 방법을 project.json 의 uses 에 적어 주세요)"
    return f"""{BEGIN}
## 이렇게 활용할 수 있어요
{uses}

## 모바일(휴대폰)에서 바로 쓰기
{LAB_URL} 를 열고 '{cfg['title']}' 카드를 눌러 값을 바꾼 뒤 **실행**을 누른다. 서버가 필요 없고, 처음 실행은 파이썬을 내려받느라 10~20초 걸린다.

## 내 컴퓨터에서 시험·실행
```
make test      # 자동 시험 (python3 -m unittest -v test_project)
make run       # 웹 화면 실행 -> http://localhost:8000 (PORT=9000 make run 으로 포트 변경)
```
- 파이썬 코드에서 직접 부르기: `from {cfg['entry'].split(':')[0]} import {cfg['entry'].split(':')[1]}; {cfg['entry'].split(':')[1]}({{...}})`
- 다른 프로그램에서 부르기: `GET http://localhost:8000/api/run?키=값` (JSON 응답), 상태 확인은 `/health`

## 배포
```
make docker    # 컨테이너로 빌드·실행 (http://localhost:8000)
```
Dockerfile 이 있으므로 Render·Fly.io·Cloud Run 등 컨테이너를 받는 곳에 그대로 올릴 수 있다. 자세한 순서는 저장소의 docs/GUIDE.md 참고.
{END_}
"""


def update_readme(folder, cfg):
    p = os.path.join(folder, "README.md")
    text = open(p, encoding="utf-8").read() if os.path.exists(p) else f"# {cfg['title']}\n"
    block = readme_block(cfg)
    if BEGIN in text:
        text = text[: text.index(BEGIN)] + block + text[text.index(END_) + len(END_) + 1:]
    else:
        text = text.rstrip() + "\n\n" + block
    open(p, "w", encoding="utf-8").write(text)


def main(folder):
    cfg = json.load(open(os.path.join(folder, "project.json"), encoding="utf-8"))
    files = {
        "server.py": SERVER,
        "test_project.py": TEST,
        "Makefile": MAKEFILE.format(name=cfg["name"]),
        "Dockerfile": DOCKERFILE,
        "requirements.txt": "\n".join(cfg.get("requirements", [])) + ("\n" if cfg.get("requirements") else "# 추가로 설치할 패키지 없음\n"),
        ".dockerignore": "__pycache__\n*.pyc\n",
    }
    for name, body in files.items():
        with open(os.path.join(folder, name), "w", encoding="utf-8") as f:
            f.write(body)
    update_readme(folder, cfg)
    print("만들었습니다:", folder, sorted(files), "+ README 표준 구역")


if __name__ == "__main__":
    for d in sys.argv[1:]:
        main(d)
