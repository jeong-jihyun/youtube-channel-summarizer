"""모바일에서 바로 쓰는 '실험실' 웹페이지를 만든다. 서버 없이 브라우저 안에서 파이썬(Pyodide)이 프로젝트를 직접 실행한다.
사용법:  python3 scripts/build_lab.py <출력폴더>      예) python3 scripts/build_lab.py lab
출력폴더를 정적 호스팅(GitHub Pages 등)에 올리면 휴대폰 주소창에서 열어 입력값을 바꾸고 실행할 수 있다.
프로젝트 목록은 projects/*/*/project.json 에서 자동으로 읽는다(새 프로젝트는 project.json 만 있으면 자동 포함)."""
import glob
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYODIDE = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/"

HTML = r'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>요약 프로젝트 실험실</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--tx:#1c1f24;--sub:#5d6673;--ac:#2563eb;--ok:#15803d;--bad:#b91c1c;--bd:#e3e6ea}
@media(prefers-color-scheme:dark){:root{--bg:#14171c;--card:#1d2128;--tx:#eceff4;--sub:#9aa4b2;--ac:#6aa0ff;--ok:#4ade80;--bad:#f87171;--bd:#2c323b}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);font:16px/1.55 -apple-system,"Noto Sans KR",sans-serif;padding:0 16px 80px}
header{padding:20px 0 8px}h1{font-size:1.35rem;margin:0}p.sub{color:var(--sub);margin:.3rem 0 0;font-size:.92rem}
.card{background:var(--card);border:1px solid var(--bd);border-radius:14px;margin:14px 0;overflow:hidden}
.card>summary{list-style:none;padding:16px;cursor:pointer;min-height:56px}.card>summary::-webkit-details-marker{display:none}
.tag{display:inline-block;font-size:.75rem;color:var(--sub);border:1px solid var(--bd);border-radius:20px;padding:1px 9px;margin-right:6px}
.t{font-weight:700;margin-top:6px}.body{padding:0 16px 16px}
h3{font-size:.95rem;margin:14px 0 6px}ul{margin:0;padding-left:1.2rem}li{margin:3px 0}
label{display:block;font-size:.88rem;color:var(--sub);margin:12px 0 4px}
input,textarea{width:100%;font:inherit;padding:12px;border:1px solid var(--bd);border-radius:10px;background:var(--bg);color:var(--tx)}textarea{min-height:110px}
button{font:inherit;font-weight:700;min-height:48px;padding:0 18px;border-radius:12px;border:0;background:var(--ac);color:#fff;margin:14px 8px 0 0}
button.g{background:transparent;color:var(--ac);border:1px solid var(--ac)}
.st{font-size:.9rem;margin-top:10px;color:var(--sub)}.ok{color:var(--ok)}.bad{color:var(--bad)}
pre{background:var(--bg);border:1px solid var(--bd);border-radius:10px;padding:12px;overflow:auto;white-space:pre-wrap;word-break:break-word;font-size:.82rem;max-height:320px}
img{max-width:100%;border-radius:10px;margin-top:10px}a{color:var(--ac)}
</style></head><body>
<header><h1>요약 프로젝트 실험실</h1>
<p class="sub">CONNECT AI LAB 영상에서 만든 모의 프로젝트를 휴대폰에서 바로 실행합니다. 서버 없이 이 화면 안에서 파이썬이 돌아갑니다. 처음 실행은 파이썬을 내려받느라 10~20초 걸립니다.</p></header>
<div id="list"></div>
<p class="sub">소스: <a href="https://github.com/jeong-jihyun/youtube-channel-summarizer">github.com/jeong-jihyun/youtube-channel-summarizer</a> · 모든 값은 모의(가짜) 데이터입니다.</p>
<script>
const PROJECTS = __PROJECTS__;
const PYODIDE_URL = "__PYODIDE__";
let pyPromise = null;
const loaded = {};
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

function loadPy(setStatus){
  if(!pyPromise){
    pyPromise = new Promise((res, rej) => {
      setStatus('파이썬을 준비하는 중... (처음 1회)');
      const s = document.createElement('script'); s.src = PYODIDE_URL + 'pyodide.js';
      s.onload = async () => { try { res(await loadPyodide({indexURL: PYODIDE_URL})); } catch(e){ rej(e); } };
      s.onerror = () => rej(new Error('파이썬 실행기를 내려받지 못했습니다. 인터넷 연결을 확인하세요.'));
      document.head.appendChild(s);
    });
  }
  return pyPromise;
}

async function prepare(p, py, setStatus){
  if(loaded[p.name]) return;
  if(p.requirements.length){ setStatus('필요한 패키지 설치 중: ' + p.requirements.join(', ')); await py.loadPackage(p.requirements); }
  const dir = '/proj/' + p.name; py.FS.mkdirTree(dir);
  for(const f of p.files){
    const r = await fetch('projects/' + p.name + '/' + f); if(!r.ok) throw new Error(f + ' 을 불러오지 못했습니다');
    py.FS.writeFile(dir + '/' + f, await r.text());
  }
  loaded[p.name] = true;
}

async function runProject(p, root){
  const st = root.querySelector('.st'), out = root.querySelector('pre'), img = root.querySelector('.img'), acts = root.querySelector('.acts');
  const setStatus = (t, cls) => { st.textContent = t; st.className = 'st ' + (cls || ''); };
  const params = {}; root.querySelectorAll('[data-k]').forEach(e => params[e.dataset.k] = e.value);
  img.innerHTML = ''; acts.innerHTML = ''; out.textContent = '';
  try{
    const py = await loadPy(setStatus); await prepare(p, py, setStatus); setStatus('실행 중...');
    py.globals.set('P_DIR', '/proj/' + p.name); py.globals.set('P_ENTRY', p.entry); py.globals.set('P_PARAMS', JSON.stringify(params));
    const txt = await py.runPythonAsync(`
import sys, json, importlib
if P_DIR not in sys.path: sys.path.insert(0, P_DIR)
m, f = P_ENTRY.split(":")
try:
    r = getattr(importlib.import_module(m), f)(json.loads(P_PARAMS))
except Exception as e:
    r = {"ok": False, "error": str(e)}
json.dumps(r, ensure_ascii=False)`);
    const j = JSON.parse(txt);
    setStatus(j.ok ? '성공' : '실패: ' + (j.error || '결과를 확인하세요'), j.ok ? 'ok' : 'bad');
    if(j.gif_base64){ img.innerHTML = '<img alt="렌더 결과" src="data:image/gif;base64,' + j.gif_base64 + '">'; j.gif_base64 = '(그림 데이터 생략)'; }
    if(j.ics){ const b = document.createElement('button'); b.textContent = '달력 파일(.ics) 받기'; b.onclick = () => {
      const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([j.ics], {type:'text/calendar'})); a.download = 'night_school.ics'; a.click(); }; acts.appendChild(b); j.ics = '(' + j.ics_lines + '줄, 위 버튼으로 받기)'; }
    const md = j.markdown || j.weekly_markdown;
    if(md){ const b = document.createElement('button'); b.className = 'g'; b.textContent = '표 복사'; b.onclick = async () => { try{ await navigator.clipboard.writeText(md); b.textContent = '복사됨'; }catch(e){ b.textContent = '복사 실패'; } }; acts.appendChild(b); }
    if(j.text){ const b = document.createElement('button'); b.className = 'g'; b.textContent = '결과 복사'; b.onclick = async () => { try{ await navigator.clipboard.writeText(j.master_prompt || j.prompt || j.text); b.textContent = '복사됨'; }catch(e){ b.textContent = '복사 실패'; } }; acts.appendChild(b); out.textContent = j.text || j.prompt; }
    else out.textContent = JSON.stringify(j, null, 2);
  }catch(e){ setStatus('오류: ' + e.message, 'bad'); }
}

function field(i){
  const a = 'data-k="' + esc(i.key) + '" value="' + esc(i.default) + '"';
  const lab = '<label>' + esc(i.label) + '</label>';
  if(i.type === 'textarea') return lab + '<textarea data-k="' + esc(i.key) + '">' + esc(i.default) + '</textarea>';
  const t = {date:'date', number:'number'}[i.type] || 'text';
  return lab + '<input type="' + t + '" inputmode="' + (t === 'number' ? 'numeric' : 'text') + '" ' + a + '>';
}

const list = document.getElementById('list');
PROJECTS.forEach((p, n) => {
  const d = document.createElement('details'); d.className = 'card'; if(n === 0) d.open = true;
  d.innerHTML = '<summary><span class="tag">' + esc(p.number) + '</span><span class="tag">' + esc(p.category) + '</span><div class="t">' + esc(p.title) + '</div></summary>' +
    '<div class="body"><p class="sub">원본 영상: <a href="https://www.youtube.com/watch?v=' + esc(p.video.id) + '">' + esc(p.video.title) + '</a></p>' +
    '<h3>이렇게 쓸 수 있어요</h3><ul>' + p.uses.map(u => '<li>' + esc(u) + '</li>').join('') + '</ul>' +
    '<h3>직접 해 보기</h3>' + p.inputs.map(field).join('') +
    '<button class="run">실행</button><div class="acts" style="display:inline"></div><div class="st"></div><div class="img"></div><pre>(아직 실행 안 함)</pre></div>';
  d.querySelector('.run').onclick = () => runProject(p, d);
  list.appendChild(d);
});
</script></body></html>
'''


def main(out):
    projects = []
    for cfg in sorted(glob.glob(os.path.join(ROOT, "projects", "*", "*", "project.json"))):
        folder = os.path.dirname(cfg)
        d = json.load(open(cfg, encoding="utf-8"))
        rel = os.path.relpath(folder, os.path.join(ROOT, "projects")).split(os.sep)
        d["category"], d["number"] = rel[0], rel[1].split("-")[0]
        d.setdefault("uses", []); d.setdefault("inputs", []); d.setdefault("video", {"id": "", "title": ""})
        dest = os.path.join(out, "projects", d["name"])
        os.makedirs(dest, exist_ok=True)
        for f in d["files"]:
            shutil.copy(os.path.join(folder, f), os.path.join(dest, f))
        projects.append({k: d[k] for k in ("name", "title", "entry", "files", "requirements", "category", "number", "uses", "inputs", "video")})
    projects.sort(key=lambda x: x["number"])
    html = HTML.replace("__PROJECTS__", json.dumps(projects, ensure_ascii=False)).replace("__PYODIDE__", PYODIDE)
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(html)
    print(f"실험실 만들기 완료: {out} (프로젝트 {len(projects)}개)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "lab")
