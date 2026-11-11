"""AI 야학당 일정표 생성기: 월~금 20:00 공개 라이브, 토~일 멤버십 일정을 만들어
달력 파일(.ics)과 요약 표(.md)로 저장한다. 표준 라이브러리만 사용."""
import datetime as dt
import sys

START, END = dt.date(2026, 11, 11), dt.date(2026, 12, 31)
KST = "Asia/Seoul"

def sessions(start=START, end=END):
    d = start
    while d <= end:
        if d.weekday() < 5:
            yield d, "공개 라이브(입문자)", dt.time(20, 0)
        else:
            yield d, "멤버십 전용(프로젝트)", dt.time(20, 0)
        d += dt.timedelta(days=1)

def to_ics(items):
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//mock-night-school//KO"]
    for d, title, t in items:
        s = dt.datetime.combine(d, t)
        e = s + dt.timedelta(hours=1)
        lines += ["BEGIN:VEVENT",
                  f"UID:night-{d.isoformat()}@mock",
                  f"DTSTART;TZID={KST}:{s:%Y%m%dT%H%M%S}",
                  f"DTEND;TZID={KST}:{e:%Y%m%dT%H%M%S}",
                  f"SUMMARY:AI 야학당 - {title}",
                  "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"

def weekly_table(items):
    rows = ["| 주 시작(월) | 공개 | 멤버십 |", "|---|---|---|"]
    weeks = {}
    for d, title, _ in items:
        monday = d - dt.timedelta(days=d.weekday())
        w = weeks.setdefault(monday, [0, 0])
        w[0 if d.weekday() < 5 else 1] += 1
    for m, (pub, mem) in sorted(weeks.items()):
        rows.append(f"| {m} | {pub} | {mem} |")
    return "\n".join(rows)


def api(params=None):
    """params: {"start": "2026-11-11", "end": "2026-12-31", "hour": "20"}"""
    p = params or {}
    start = dt.date.fromisoformat(p.get("start", START.isoformat()))
    end = dt.date.fromisoformat(p.get("end", END.isoformat()))
    items = list(sessions(start, end))
    ics = to_ics(items)
    pub = sum(1 for _, t, _ in items if t.startswith("공개"))
    return {"ok": len(items) > 0, "total": len(items), "public": pub, "members": len(items) - pub,
            "weekly_markdown": weekly_table(items), "ics_head": ics.splitlines()[:8], "ics_lines": len(ics.splitlines()), "ics": ics}

if __name__ == "__main__":
    items = list(sessions())
    open("night_school.ics", "w", encoding="utf-8", newline="").write(to_ics(items))
    table = weekly_table(items)
    open("weekly.md", "w", encoding="utf-8").write(table + "\n")
    pub = sum(1 for _, t, _ in items if t.startswith("공개"))
    print(f"전체 {len(items)}회 (공개 {pub}, 멤버십 {len(items) - pub})")
    print(table.splitlines()[0]); print(*table.splitlines()[2:5], sep="\n")
    assert items[0][0] == dt.date(2026, 11, 11) and items[0][0].weekday() == 2  # 수요일 시작
    print("성공")
