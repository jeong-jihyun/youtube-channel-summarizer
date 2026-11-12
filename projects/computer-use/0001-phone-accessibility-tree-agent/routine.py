"""스마트폰 유즈 루틴 키트 (영상 K4QdeGqTSfQ, THE FOUNDER EP.2).

영상이 보여 준 방식: 폰을 컴퓨터에 미러링(아이폰 미러링 등)하고, AI(ChatGPT·Claude·Antigravity)가
화면을 보고 눌러서 스레드 글쓰기·쿠팡 장바구니·네이버 블로그를 처리한다. 영상의 결론은
'실시간으로 지켜보지 말고 루틴(시간표)으로 촘촘히 적어 맡겨라'.
이 파일은 내 루틴(시간, 앱, 할 일)을 넣으면
  1) 시간순 하루 시간표와 그대로 붙여 넣을 AI 지시문을 만들고,
  2) 앱마다 화면 읽는 방법(접근성 트리 -> 스크린샷, 웹은 HTML)과 토큰 비용 어림을 알려 주고,
  3) 결제·로그인·매매처럼 사람이 확인해야 할 단계를 표시한다(안전장치: 영상에는 없는 제안).
연습용 가짜 폰(agent.py)으로 '화면을 JSON으로 읽고 행동 고르기'를 직접 돌려 볼 수도 있다."""
import re
import sys

LINE = re.compile(r"^(\d{1,2}):(\d{2})\s+(\S+)\s+(.+)$")
# 앱 이름 -> (종류, 메모). 종류: web=브라우저로 열림, app=폰 앱(미러링)
APPS = {
    "threads": ("app", "스레드: 글은 텍스트 파일에 먼저 써서 복사해 붙여넣기(영상에서 ChatGPT가 쓴 방식)"),
    "스레드": ("app", "스레드: 글은 텍스트 파일에 먼저 써서 복사해 붙여넣기(영상에서 ChatGPT가 쓴 방식)"),
    "instagram": ("app", "인스타그램: 사진·릴스 선택 -> 음악 -> 게시 순서"),
    "인스타": ("app", "인스타그램: 사진·릴스 선택 -> 음악 -> 게시 순서"),
    "coupang": ("app", "쿠팡: 상품 비교 후 장바구니까지, 가격 비교 리포트 페이지를 따로 만들게 함"),
    "쿠팡": ("app", "쿠팡: 상품 비교 후 장바구니까지, 가격 비교 리포트 페이지를 따로 만들게 함"),
    "naver": ("app", "네이버 블로그: 앱이 없으면 앱 설치부터 시킴, 제목·본문은 텍스트 파일로 만든 뒤 붙여넣고 카테고리 선택 후 발행"),
    "네이버": ("app", "네이버 블로그: 앱이 없으면 앱 설치부터 시킴, 제목·본문은 텍스트 파일로 만든 뒤 붙여넣고 카테고리 선택 후 발행"),
    "chrome": ("web", "브라우저: HTML을 직접 읽으므로 가장 빠르고 토큰이 적음"),
    "크롬": ("web", "브라우저: HTML을 직접 읽으므로 가장 빠르고 토큰이 적음"),
}
RISK = (("구매", "결제·주문 확정"), ("결제", "결제·주문 확정"), ("주문", "결제·주문 확정"), ("송금", "송금"), ("매수", "주식·코인 매매"), ("매도", "주식·코인 매매"),
        ("코인", "주식·코인 매매"), ("주식", "주식·코인 매매"), ("로그인", "로그인·비밀번호"), ("비밀번호", "로그인·비밀번호"), ("삭제", "삭제"))
AI = {
    "chatgpt": "영상 평가: 컴퓨터 유즈가 가장 빠르고 잘 됨. 텍스트 파일에 먼저 쓰고 복사하는 방식으로 입력 문제를 풀었다.",
    "antigravity": "영상 평가: 잘 되지만 조금 느림. 접근이 안정적(스레드·네이버에 스스로 들어감).",
    "claude": "영상 평가: 컴퓨터 유즈로 마우스 이동 등 기본 동작이 됨. 이 영상에서 폰 장시간 작업 비교는 ChatGPT·Antigravity가 중심.",
}
# 방식별 한 화면당 토큰 어림(가정값, 영상은 '스크린샷이 훨씬 많이 든다'고만 설명)
TOKENS = {"접근성 트리(JSON)": 800, "HTML 읽기": 1500, "스크린샷": 3000}
DEFAULT = ("08:00 threads 오늘의 컴퓨터 유즈 소식을 3줄로 글 쓰고 게시\n"
           "09:00 쿠팡 닭가슴살 가격 비교해서 가장 싼 것 장바구니에 담기\n"
           "10:00 네이버 블로그에 '자동화 입문' 글 작성 후 발행\n"
           "12:00 인스타 오늘 찍은 강아지 영상 릴스로 올리기")


def parse(text):
    items, bad = [], []
    for raw in (text or "").splitlines():
        s = raw.strip()
        if not s:
            continue
        m = LINE.match(s)
        if not m or not (0 <= int(m.group(1)) < 24 and 0 <= int(m.group(2)) < 60):
            bad.append(s)
            continue
        app = m.group(3)
        kind, note = APPS.get(app.lower(), APPS.get(app, ("app", "알 수 없는 앱: 홈 화면에서 앱 이름으로 검색해 여는 단계부터 시키기")))
        task = m.group(4)
        risks = sorted({label for key, label in RISK if key in task})
        items.append({"time": f"{int(m.group(1)):02d}:{m.group(2)}", "app": app, "kind": kind, "task": task, "note": note, "risks": risks})
    items.sort(key=lambda i: i["time"])
    return items, bad


def plan(item, mirror):
    if item["kind"] == "web":
        return ["HTML 읽기"]
    # 미러링 창은 한 장의 그림이라 접근성 트리가 안 잡히는 경우가 많다(추정). 영상에서도 화면을 캡처해 읽는다.
    return ["접근성 트리(JSON)", "스크린샷"] if "접근성" in mirror else ["스크린샷"]


def prompt_for(item, mirror):
    risk = ""
    if item["risks"]:
        risk = f"\n  단, {'·'.join(item['risks'])} 단계에 오면 멈추고 나에게 확인을 요청해 줘."
    return (f"{item['time']} [{item['app']}] {item['task']}\n"
            f"  {mirror} 화면에서 컴퓨터 유즈로 진행해. 화면을 보고 누를 곳을 고르고, 눌린 뒤에는 바뀐 화면을 확인해.\n"
            f"  입력이 잘 안 되는 글자는 텍스트 파일에 먼저 쓰고 복사해서 붙여넣어. 끝나면 결과를 한 줄로 보고해." + risk)


def api(params=None):
    p = params or {}
    mirror = (p.get("mirror") or "아이폰 미러링").strip()
    ai = (p.get("ai") or "chatgpt").strip().lower()
    items, bad = parse(p.get("routines") or DEFAULT)
    if not items:
        return {"ok": False, "error": "루틴은 한 줄에 '08:00 앱이름 할 일' 형식으로 입력하세요. 읽지 못한 줄: " + "; ".join(bad[:3])}
    screens = int(float(p.get("screens") or 12))
    rows = []
    total_tokens = 0
    for it in items:
        steps = plan(it, mirror)
        first = TOKENS[steps[0]]
        worst = TOKENS[steps[-1]]
        it["perception"] = " -> ".join(steps)
        it["tokens_best"], it["tokens_worst"] = first * screens, worst * screens
        total_tokens += it["tokens_worst"]
        rows.append(it)
    master = (f"아래 하루 루틴을 시간표대로 {mirror}(으)로 처리해 줘. 실시간으로 지켜보지 않을 거야. "
              "각 항목이 끝나면 결과를 한 줄로 기록하고, 막히면 이유를 적고 다음 항목으로 넘어가.\n\n"
              + "\n".join(prompt_for(i, mirror) for i in rows))
    lines = [f"[하루 시간표] {mirror}, 사용 AI: {ai}"]
    lines += [f"  {i['time']}  {i['app']}  {i['task']}" + (f"   !! 사람 확인: {', '.join(i['risks'])}" if i["risks"] else "") for i in rows]
    lines += ["", "[화면 읽는 방법과 토큰 어림(화면 %d장 기준, 가정값)]" % screens]
    lines += [f"  {i['time']} {i['app']}: {i['perception']} / " + (f"약 {i['tokens_worst']:,} 토큰" if i["tokens_best"] == i["tokens_worst"] else f"최소 {i['tokens_best']:,} ~ 최대 {i['tokens_worst']:,} 토큰") for i in rows]
    lines += ["", "[앱별 메모]"] + [f"  {i['note']}" for i in rows]
    lines += ["", "[AI 고르기] " + AI.get(ai, "목록에 없는 AI입니다. chatgpt, antigravity, claude 중에서 고르세요.")]
    lines += ["", "[붙여 넣을 지시문]", master]
    return {"ok": True, "text": "\n".join(lines), "items": rows, "unread_lines": bad, "total_tokens_worst": total_tokens,
            "needs_human": [i["time"] + " " + i["app"] for i in rows if i["risks"]], "master_prompt": master}


if __name__ == "__main__":
    r = api({})
    print(r["text"])
    assert r["ok"] and len(r["items"]) == 4 and r["items"][0]["time"] == "08:00"
    assert r["needs_human"] == [] and "스크린샷" in r["items"][0]["perception"]
    assert api({"routines": "09:00 쿠팡 닭가슴살 결제까지 진행"})["needs_human"] == ["09:00 쿠팡"]
    assert api({"mirror": "접근성 가능한 안드로이드"})["items"][0]["perception"] == "접근성 트리(JSON) -> 스크린샷"
    b = api({"routines": "07:30 threads 코인 매수해줘\n잘못된줄\n25:00 x y"})
    assert b["ok"] and b["needs_human"] == ["07:30 threads"] and len(b["unread_lines"]) == 2
    assert api({"routines": "그냥 글"})["ok"] is False
    w = api({"routines": "08:00 크롬 뉴스 검색해서 요약"})["items"][0]
    assert w["perception"] == "HTML 읽기" and w["tokens_worst"] < api({"routines": "08:00 threads 글쓰기"})["items"][0]["tokens_worst"]
    print("성공")
    sys.exit(0)
