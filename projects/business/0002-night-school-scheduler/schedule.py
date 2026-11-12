"""AI 야학당 수강 플래너 (영상 0Hif6Y40uC8).

영상 내용: 11월 11일(수) 시작, 11~12월 두 달. 월~금 저녁 8시 무료 공개 라이브(입문자 위주),
토~일은 멤버십 전용 심화(함께 프로젝트, 주 2회). 주제는 '인공지능 자율화 회사 만들기'이고
이론·실습·개발·자동화·자율화·에이전트와 AI 1인 기업 분석을 다룬다(생존·수익화·기회).
일정은 외부 일정으로 조금씩 바뀔 수 있고, 변경은 채널 게시글로 알려 준다(알림 설정 필요).

이 파일이 하는 일
  1) 달력 파일(.ics): 알림(미리 N분)과 설명이 들어 있고, 일정마다 고정 UID라 다시 가져오면 갱신된다.
     멤버십이 아니면 토·일은 넣지 않는다.
  2) 출석한 날짜를 넣으면 출석률·연속 출석·이번 주 남은 횟수를 계산한다.
  3) 매 회차 배운 것을 남길 학습 기록 양식을 만든다.
표준 라이브러리만 사용."""
import datetime as dt
import re
import sys

START, END = dt.date(2026, 11, 11), dt.date(2026, 12, 31)
KST = "Asia/Seoul"
TOPICS = "이론·실습·개발·자동화·자율화·에이전트·AI 1인 기업 분석"
THEME = "인공지능 자율화 회사 만들기"
NOTE = "일정은 사정으로 바뀔 수 있음. 변경은 채널 게시글로 공지되니 구독과 알림 설정을 해 두세요."
CHANNEL = "https://www.youtube.com/@CONNECT-AI-LAB"


def is_public(d):
    return d.weekday() < 5


def sessions(start=START, end=END, member=False):
    d = start
    while d <= end:
        if is_public(d):
            yield d, "공개 라이브(입문자)", dt.time(20, 0)
        elif member:
            yield d, "멤버십 전용(프로젝트)", dt.time(20, 0)
        d += dt.timedelta(days=1)


def to_ics(items, alarm_min=30):
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//night-school-planner//KO", "CALSCALE:GREGORIAN"]
    for d, title, t in items:
        s = dt.datetime.combine(d, t)
        e = s + dt.timedelta(hours=1)
        lines += ["BEGIN:VEVENT",
                  f"UID:night-{d.isoformat()}@night-school-planner",
                  f"DTSTAMP:{dt.datetime(2026, 11, 11, 0, 0):%Y%m%dT%H%M%SZ}",
                  f"DTSTART;TZID={KST}:{s:%Y%m%dT%H%M%S}",
                  f"DTEND;TZID={KST}:{e:%Y%m%dT%H%M%S}",
                  f"SUMMARY:AI 야학당 - {title}",
                  f"DESCRIPTION:주제 {THEME}. {NOTE}",
                  f"URL:{CHANNEL}",
                  "BEGIN:VALARM", "ACTION:DISPLAY", "DESCRIPTION:AI 야학당 시작 전", f"TRIGGER:-PT{int(alarm_min)}M", "END:VALARM",
                  "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def parse_dates(text):
    """'2026-11-11, 2026-11-12' 또는 줄바꿈, '2026-11-11~2026-11-14' 범위도 허용. 읽지 못한 조각도 돌려준다."""
    out, bad = set(), []
    for tok in re.split(r"[,\n ]+", text or ""):
        tok = tok.strip()
        if not tok:
            continue
        try:
            if "~" in tok:
                a, b = (dt.date.fromisoformat(x) for x in tok.split("~", 1))
                if b < a:
                    raise ValueError
                out.update(a + dt.timedelta(days=i) for i in range((b - a).days + 1))
            else:
                out.add(dt.date.fromisoformat(tok))
        except ValueError:
            bad.append(tok)
    return out, bad


def progress(items, attended, today):
    due = [d for d, _, _ in items if d <= today]
    got = [d for d in due if d in attended]
    streak = 0
    for d in reversed(due):
        if d in attended:
            streak += 1
        else:
            break
    monday = today - dt.timedelta(days=today.weekday())
    week = [d for d, _, _ in items if monday <= d < monday + dt.timedelta(days=7)]
    return {"지난 회차": len(due), "출석": len(got), "출석률(%)": round(100 * len(got) / len(due)) if due else 0,
            "연속 출석": streak, "이번 주 남은 회차": len([d for d in week if d > today])}


def log_template(d):
    return (f"## {d:%Y-%m-%d} ({'월화수목금토일'[d.weekday()]})\n- 오늘 배운 것 한 줄:\n- 내 일/생활에 써먹을 것 한 가지:\n"
            f"- 해 본 실습(링크·결과):\n- 모르겠는 것(다음에 질문):\n- 분야 체크(이론·실습·개발·자동화·자율화·에이전트·1인 기업): [ ]")


def weekly_table(items):
    rows = ["| 주 시작(월) | 공개 | 멤버십 |", "|---|---|---|"]
    weeks = {}
    for d, title, _ in items:
        monday = d - dt.timedelta(days=d.weekday())
        w = weeks.setdefault(monday, [0, 0])
        w[0 if is_public(d) else 1] += 1
    for m, (pub, mem) in sorted(weeks.items()):
        rows.append(f"| {m} | {pub} | {mem} |")
    return "\n".join(rows)


def api(params=None):
    p = params or {}
    try:
        start = dt.date.fromisoformat(p.get("start") or START.isoformat())
        end = dt.date.fromisoformat(p.get("end") or END.isoformat())
        today = dt.date.fromisoformat(p.get("today") or "2026-11-20")
        alarm = int(float(p.get("alarm") or 30))
    except ValueError:
        return {"ok": False, "error": "날짜는 2026-11-11 형식, 알림은 숫자(분)로 입력하세요."}
    if end < start:
        return {"ok": False, "error": "끝나는 날이 시작일보다 빠릅니다."}
    member = str(p.get("member") or "아니오").strip() in ("예", "멤버십", "yes", "Y", "true")
    items = list(sessions(start, end, member))
    if not items:
        return {"ok": False, "error": "이 기간에 해당하는 회차가 없습니다(멤버십이 아니면 주말은 제외)."}
    attended, bad = parse_dates(p.get("attended", "2026-11-11, 2026-11-12, 2026-11-13, 2026-11-16, 2026-11-18"))
    pr = progress(items, attended, today)
    ics = to_ics(items, alarm)
    pub = sum(1 for d, _, _ in items if is_public(d))
    lines = [f"[야학당 일정] {start} ~ {end}: 총 {len(items)}회 (공개 {pub}, 멤버십 {len(items) - pub}) / 멤버십 {'포함' if member else '제외'}",
             f"  매일 20:00 시작, 알림 {alarm}분 전. 주제: {THEME}. 다루는 것: {TOPICS}.",
             f"  {NOTE}",
             f"[{today} 기준 출석] {pr['출석']}/{pr['지난 회차']}회 ({pr['출석률(%)']}%), 연속 {pr['연속 출석']}회, 이번 주 남은 회차 {pr['이번 주 남은 회차']}회"]
    if bad:
        lines.append("  읽지 못한 날짜: " + ", ".join(bad))
    nxt = next((d for d, _, _ in items if d >= today), None)
    if nxt:
        lines += ["", "[다음 회차 학습 기록 양식]", log_template(nxt)]
    return {"ok": True, "text": "\n".join(lines), "total": len(items), "public": pub, "members": len(items) - pub,
            "progress": pr, "unread_dates": bad, "weekly_markdown": weekly_table(items),
            "ics_lines": len(ics.splitlines()), "ics": ics}


if __name__ == "__main__":
    items = list(sessions())
    assert items[0][0] == dt.date(2026, 11, 11) and items[0][0].weekday() == 2  # 수요일 시작
    assert all(d.weekday() < 5 for d, _, _ in items) and len(items) == 37, len(items)  # 11/11~12/31 평일
    mem = list(sessions(member=True))
    assert len(mem) == 51 and len(mem) - len(items) == 14  # 주말 14일
    r = api({})
    print(r["text"])
    assert r["ok"] and r["progress"]["출석"] == 5 and r["progress"]["지난 회차"] == 8 and r["progress"]["연속 출석"] == 0
    ics = r["ics"]
    assert ics.count("BEGIN:VEVENT") == 37 and ics.count("TRIGGER:-PT30M") == 37 and "TZID=Asia/Seoul" in ics
    assert api({"member": "예"})["ics"].count("BEGIN:VEVENT") == 51
    rng, bad = parse_dates("2026-11-11~2026-11-13, 가짜")
    assert len(rng) == 3 and bad == ["가짜"]
    assert api({"start": "2026-12-31", "end": "2026-11-11"})["ok"] is False and api({"start": "x"})["ok"] is False
    open("night_school.ics", "w", encoding="utf-8", newline="").write(ics)
    print("성공")
    sys.exit(0)
