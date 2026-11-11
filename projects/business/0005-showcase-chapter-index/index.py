"""설명란의 챕터 목록(시간 + 제목)을 읽어 바로가기 링크가 달린 색인과 통계를 만든다.
샘플 입력은 영상 설명란에서 가져온 챕터 일부(chapters_sample.txt)."""
import re
import sys

VIDEO = "https://www.youtube.com/watch?v=aE7oIEgoNsw"
LINE = re.compile(r"^(?:(\d+):)?(\d{1,2}):(\d{2})\s+(.+)$")

def parse(text):
    out = []
    for raw in text.splitlines():
        m = LINE.match(raw.strip())
        if not m:
            continue
        h, mi, s, title = int(m.group(1) or 0), int(m.group(2)), int(m.group(3)), m.group(4)
        name, _, tagline = title.partition(":")
        out.append({"sec": h * 3600 + mi * 60 + s, "name": name.strip(), "tagline": tagline.strip()})
    return out

def link(sec):
    return f"{VIDEO}&t={sec}s"

def to_markdown(items):
    rows = ["| 시작 | 서비스 | 한 줄 | 길이(분) | 링크 |", "|---|---|---|---|---|"]
    for i, c in enumerate(items):
        nxt = items[i + 1]["sec"] if i + 1 < len(items) else None
        mins = f"{(nxt - c['sec']) / 60:.1f}" if nxt else "-"
        t = f"{c['sec'] // 3600}:{c['sec'] % 3600 // 60:02d}:{c['sec'] % 60:02d}"
        rows.append(f"| {t} | {c['name']} | {c['tagline']} | {mins} | [이동]({link(c['sec'])}) |")
    return "\n".join(rows)


def api(params=None):
    """params: {"chapters": "0:00 인트로: ...\n3:17 서비스: 한 줄", "video": "영상ID"}  (없으면 샘플 사용)"""
    import os
    global VIDEO
    p = params or {}
    text = p.get("chapters") or open(os.path.join(os.path.dirname(__file__), "chapters_sample.txt"), encoding="utf-8").read()
    if p.get("video"):
        VIDEO = "https://www.youtube.com/watch?v=" + p["video"]
    items = parse(text)
    return {"ok": len(items) > 0, "count": len(items), "markdown": to_markdown(items), "first": items[0] if items else None}

if __name__ == "__main__":
    items = parse(open("chapters_sample.txt", encoding="utf-8").read())
    print(to_markdown(items))
    longest = max(zip(items, items[1:]), key=lambda p: p[1]["sec"] - p[0]["sec"])
    print("가장 오래 다룬 서비스:", longest[0]["name"])
    assert len(items) == 12 and items[0]["sec"] == 0 and items[3]["sec"] == 8 * 60 + 31
    print("성공")
