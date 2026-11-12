"""AI 1인 기업 서비스 점검표 + 쇼케이스 색인 (영상 aE7oIEgoNsw, 4시간 52분).

영상에서 멘토가 129명 중 61개 서비스를 보며 반복해서 한 말(타겟을 니치하게, 돈 내는 곳으로, 가격·결제·수익 모델,
AI를 제대로 쓰기)을 점검표로 옮겼다. 내 서비스 정보를 넣으면 점수와 '멘토라면 이렇게 말했을 것' 피드백을 준다.
각 피드백에는 영상 속 실제 사례(시간 링크)를 붙였다. 또 영상 설명란의 챕터 전체(chapters_full.txt)를 색인으로 검색할 수 있다.

주의: 점검 규칙은 영상 설명란 전체와 자막의 일부(대표 사례 약 15곳)에서 뽑은 경험칙이다. 멘토의 공식 평가 기준이 아니다.
"""
import os
import re
import sys

VID = "aE7oIEgoNsw"
LINE = re.compile(r"^(?:(\d+):)?(\d{1,2}):(\d{2})\s+(.+)$")
HERE = os.path.dirname(os.path.abspath(__file__))

# 영상 속 실제 사례(제목, 초)
CASES = {
    "jewelry": ("아우라 주얼리: 일반인 대신 주얼리 샵에 팔기", 197),
    "gogo": ("고고스타트: 2,900원은 너무 싸다(사업자 대상)", 511),
    "etymology": ("어원 영단어: 수익 모델(돈)이 안 보인다", 763),
    "fortune": ("돈방석: 유료 리포트인데 가격이 안 나와 있다", 2394),
    "starlord": ("스타로드 K팝: 더 키우지 말고 광고 붙여 완성", 5570),
    "niche": ("틈새 헌터: 무료 뉴스레터 + 유료 개인화 구독", 5860),
    "music": ("뮤직벙커: 돈이 모이는 곳에 만들기", 6117),
    "letter": ("레터 언박싱: 타겟이 없다", 8706),
    "typing": ("타닥런: 타겟을 니치하게(수험생 등)", 9541),
    "memory": ("기억을 작품으로: 99,000원인데 뭘 받는지 모르겠다", 10710),
    "dreamcut": ("드림컷: 모델 이름 지정·입력을 프롬프트로", 12601),
    "event": ("CHECK MY EVENT: 니치하고 좋다, 결제 페이지 확인", 16867),
}
GENERIC = ("일반인", "누구나", "모든 사람", "모든사람", "일반 사용자", "사람들", "전체", "대중")
BUSINESS = ("샵", "사장", "업체", "학원", "병원", "유치원", "어린이집", "플래너", "셀러", "사업자", "기관", "원장",
            "교사", "센터", "기업", "회사", "스토어", "매장", "가게", "공인중개", "보육", "복지사", "프리랜서")


def link(sec):
    return f"https://www.youtube.com/watch?v={VID}&t={int(sec)}s"


def hms(sec):
    return f"{sec // 3600}:{sec % 3600 // 60:02d}:{sec % 60:02d}"


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


def to_markdown(items, all_items=None):
    all_items = all_items or items
    nxt = {c["sec"]: (all_items[i + 1]["sec"] if i + 1 < len(all_items) else None) for i, c in enumerate(all_items)}
    rows = ["| 시작 | 서비스 | 한 줄 | 길이(분) | 링크 |", "|---|---|---|---|---|"]
    for c in items:
        n = nxt.get(c["sec"])
        mins = f"{(n - c['sec']) / 60:.1f}" if n else "-"
        rows.append(f"| {hms(c['sec'])} | {c['name']} | {c['tagline']} | {mins} | [이동]({link(c['sec'])}) |")
    return "\n".join(rows)


def _num(s):
    digits = re.sub(r"[^\d]", "", str(s or ""))
    return int(digits) if digits else None


def review(p):
    """p: name, target, money(광고/유료/구독/수수료/없음), price, includes, pay(있음/없음), ai(프롬프트/키워드/없음), model(지정/미지정)"""
    target = (p.get("target") or "").strip()
    money = (p.get("money") or "").strip()
    price = _num(p.get("price"))
    includes = (p.get("includes") or "").strip()
    pay = (p.get("pay") or "").strip()
    ai = (p.get("ai") or "").strip()
    model = (p.get("model") or "").strip()
    b2b = any(w in target for w in BUSINESS)
    generic = (not target) or any(w in target for w in GENERIC)
    paid = any(w in money for w in ("유료", "구독", "수수료", "판매"))
    ads = "광고" in money
    items = []

    def add(rule, score, mx, msg, case=None):
        ref = None
        if case:
            ref = {"사례": CASES[case][0], "시간": hms(CASES[case][1]), "링크": link(CASES[case][1])}
        items.append({"항목": rule, "점수": score, "만점": mx, "피드백": msg, "영상 속 사례": ref})

    # 1 타겟(25)
    if not target:
        add("타겟", 0, 25, "누구를 위한 서비스인지가 없습니다. 서비스 설명이 아니라 '누가 쓰는지'부터 적으세요.", "letter")
    elif generic:
        add("타겟", 8, 25, "타겟이 너무 큽니다. 일반인 전체가 아니라 아주 좁은 한 집단(예: 중간고사 1주일 전 고1)으로 좁히세요.", "typing")
    elif len(target) < 8:
        add("타겟", 16, 25, "타겟이 짧습니다. 누구가, 언제, 어떤 상황에서 쓰는지까지 한 문장으로 쓰면 더 니치해집니다.", "event")
    else:
        add("타겟", 25, 25, "타겟이 구체적입니다. 이 집단이 실제로 모여 있는 곳에서 홍보하세요.", "event")
    # 2 돈 내는 곳(15)
    if b2b:
        add("돈이 모이는 곳", 15, 15, "사업자·기관 타겟이라 지불 여력이 있습니다. 가격을 개인용보다 높게 잡아도 됩니다.", "jewelry")
    else:
        add("돈이 모이는 곳", 6, 15, "개인 소비자는 돈 내게 하기가 어렵습니다. 같은 기능을 업체(샵·학원·플래너 등)에 파는 쪽도 검토하세요.", "music")
    # 3 수익 모델(20)
    if not money or money == "없음":
        add("수익 모델", 0, 20, "돈 버는 방법이 안 보입니다. 광고, 유료 결제, 구독, 수수료 중 하나를 정하세요.", "etymology")
    elif ads and not paid:
        add("수익 모델", 14, 20, "광고 수익이면 로그인·유료 코스 같은 구조는 빼고 더 키우지 말고 완성해 광고를 붙여 공개하세요.", "starlord")
    elif "구독" in money:
        add("수익 모델", 20, 20, "구독 모델입니다. 무료로 시작해 쓰게 하고, 내 정보를 넣으면 나만의 결과를 주는 유료 단계를 두세요.", "niche")
    else:
        add("수익 모델", 18, 20, "유료 모델입니다. 무료 체험을 어디까지 줄지(예: 3개까지)와 유료 전환 지점을 정하세요.", "gogo")
    # 4 가격(15)
    if paid or price:
        if price is None:
            add("가격", 3, 15, "유료인데 가격이 화면에 안 보입니다. 가격을 먼저 보여 주세요.", "fortune")
        elif b2b and price < 5000:
            add("가격", 6, 15, f"{price:,}원은 사업자에게는 너무 쌉니다. 정부 과제 등으로 쓸 수 있다면 더 비싸도 됩니다. 경쟁사 가격도 조사하세요.", "gogo")
        elif price >= 50000 and len(includes) < 15:
            add("가격", 5, 15, f"{price:,}원인데 무엇을 받는지가 안 보이면 비싸다고 느낍니다. 포함 내용을 구체적으로 적으세요.", "memory")
        else:
            add("가격", 15, 15, "가격과 받는 내용이 맞아 보입니다. 경쟁사 가격과 한 번만 비교해 보세요.", None)
    else:
        add("가격", 8, 15, "무료 서비스라 가격 점검은 생략합니다(광고로 수익을 낼 경우 방문자 수가 관건).", "starlord")
    # 5 결제 흐름(10)
    if pay in ("있음", "연결", "테스트함", "yes", "Y"):
        add("결제 연결", 10, 10, "결제까지 이어집니다. 실제로 끝까지 눌러 결제가 되는지 직접 시험하세요.", "event")
    elif not paid:
        add("결제 연결", 7, 10, "유료 모델이 아니라 결제 연결은 필수는 아닙니다.", None)
    else:
        add("결제 연결", 0, 10, "유료인데 결제 페이지가 없습니다. 판매는 결제 페이지까지 이어져야 합니다(사업자 등록 포함).", "event")
    # 6 AI 활용(10) & 7 모델(5)
    if ai in ("프롬프트", "프롬프트 입력", "입력"):
        add("AI 활용", 10, 10, "사용자 입력을 프롬프트로 넘겨 AI가 생성합니다. 좋은 구조입니다.", "dreamcut")
    elif ai in ("키워드", "키워드 고정", "고정"):
        add("AI 활용", 3, 10, "입력값을 그대로 끼워 넣는 프로그램이 되어 있습니다. 사용자 입력을 프롬프트 입력으로 넣어 AI가 생성하게 바꾸세요.", "dreamcut")
    else:
        add("AI 활용", 5, 10, "AI를 쓰지 않는 서비스입니다. 괜찮지만 AI로 더 나아질 부분이 있는지 보세요.", None)
    if model in ("지정", "지정함", "명시"):
        add("모델 지정", 5, 5, "모델 이름을 직접 지정했습니다. 가격표도 함께 확인해 더 최근의 싼 모델이 있는지 보세요.", "dreamcut")
    elif ai in ("프롬프트", "프롬프트 입력", "입력", "키워드", "키워드 고정", "고정"):
        add("모델 지정", 1, 5, "코딩 도구에 맡기면 옛날 모델을 연결합니다. 쓰고 싶은 모델의 정확한 이름을 직접 주세요.", "dreamcut")
    else:
        add("모델 지정", 3, 5, "AI 모델을 쓰지 않아 해당 없음입니다.", None)

    total = sum(i["점수"] for i in items)
    worst = sorted((i for i in items if i["점수"] < i["만점"]), key=lambda i: i["점수"] - i["만점"])[:3]
    return {"총점": total, "만점": 100, "항목": items, "먼저 고칠 3가지": [f"{w['항목']}: {w['피드백']}" for w in worst] or ["모든 항목이 만점입니다. 실제 사용자 3명에게 보여 주고 반응을 보세요."]}


def api(params=None):
    p = params or {}
    text = open(os.path.join(HERE, "chapters_full.txt"), encoding="utf-8").read()
    items = parse(text)
    kw = (p.get("keyword") or "").strip()
    shown = [c for c in items if kw in c["name"] + c["tagline"]] if kw else items
    r = review({
        "target": p.get("target", "중간고사 일주일 전, 공부하다 졸린 고등학교 1학년"),
        "money": p.get("money", "구독"), "price": p.get("price", "4900"),
        "includes": p.get("includes", "내 교과서 문장을 넣으면 퀴즈 게임으로 바꿔 줌"),
        "pay": p.get("pay", "있음"), "ai": p.get("ai", "프롬프트"), "model": p.get("model", "지정"),
    })
    lines = [f"[점검 결과] {p.get('name', '내 서비스')}  {r['총점']}/{r['만점']}점", ""]
    for i in r["항목"]:
        lines.append(f"- {i['항목']} {i['점수']}/{i['만점']}: {i['피드백']}")
        if i["영상 속 사례"]:
            c = i["영상 속 사례"]
            lines.append(f"    영상 {c['시간']} {c['사례']}  {c['링크']}")
    lines += ["", "먼저 고칠 3가지:"] + [f"  {n}. {t}" for n, t in enumerate(r["먼저 고칠 3가지"], 1)]
    return {
        "ok": len(items) >= 60, "text": "\n".join(lines), "review": r,
        "index_count": len(items), "index_shown": len(shown),
        "markdown": to_markdown(shown, items),
    }


if __name__ == "__main__":
    items = parse(open(os.path.join(HERE, "chapters_full.txt"), encoding="utf-8").read())
    assert len(items) == 67 and items[0]["sec"] == 0 and items[1]["sec"] == 197 and items[-1]["sec"] == 4 * 3600 + 52 * 60 + 23
    good = review({"target": "수능 앞두고 졸린 고등학생", "money": "구독", "price": "4900", "includes": "교과서 문장으로 만든 퀴즈 게임",
                   "pay": "있음", "ai": "프롬프트", "model": "지정"})
    bad = review({"target": "일반인", "money": "없음", "pay": "없음", "ai": "키워드", "model": "미지정"})
    cheap = review({"target": "소규모 학원 원장", "money": "유료", "price": "2,900원", "pay": "있음"})
    assert good["총점"] >= 85 and bad["총점"] <= 35 and good["총점"] > cheap["총점"] > bad["총점"], (good["총점"], cheap["총점"], bad["총점"])
    assert any("너무 쌉니다" in i["피드백"] for i in cheap["항목"])
    assert all(i["영상 속 사례"]["링크"].startswith("https://www.youtube.com/watch?v=" + VID) for i in bad["항목"] if i["영상 속 사례"])
    r = api({"keyword": "시니어"})
    assert r["ok"] and r["index_shown"] >= 2, r["index_shown"]
    print(r["text"])
    print("성공")
    sys.exit(0)
