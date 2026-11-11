"""모든 프로젝트를 한 번에 시험한다.  python3 scripts/check_all.py
각 projects/*/*/project.json 이 있는 폴더에서 test_project.py 를 실행하고 표로 보여 준다. 하나라도 실패하면 종료 코드 1."""
import glob
import os
import subprocess
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows, failed = [], 0
for cfg in sorted(glob.glob(os.path.join(root, "projects", "*", "*", "project.json"))):
    d = os.path.dirname(cfg)
    r = subprocess.run([sys.executable, "-m", "unittest", "test_project"], cwd=d, capture_output=True, text=True, timeout=300)
    ok = r.returncode == 0
    failed += 0 if ok else 1
    rows.append((os.path.relpath(d, root), "통과" if ok else "실패"))
    if not ok:
        print(r.stderr[-800:])
w = max((len(a) for a, _ in rows), default=10)
for name, res in rows:
    print(f"{name:{w}s}  {res}")
print(f"\n전체 {len(rows)}개 중 통과 {len(rows) - failed}개")
sys.exit(1 if failed else 0)
