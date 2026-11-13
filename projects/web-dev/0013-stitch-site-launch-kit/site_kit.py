"""0원 AI 1인 사업 사이트 출시 키트 (영상 l_BNmIsuNVU, AI 1인 사업 EP.1).

영상의 순서를 점검 가능한 도구로 옮겼다(자막 전체 읽음, 영어 제공 자막).
  1) Design.md: 디자인 작업 매뉴얼 파일을 구글 Stitch 2.0에 먼저 넣는다(영상 3:38). 색·글꼴·버튼 모서리가 들어 있다.
     고칠 때는 Gemini에 '이 Design.md를 흰 배경으로 고쳐 줘'라고 시켜 새 본문을 붙여 넣는다.
  2) 페이지: 메인 -> 전자책 상세 -> 라이브러리 -> 구매 완료·다운로드. 결제 화면에서 가상화폐는 빼고 카드+PayPal만 남겼다.
  3) 결제: 영상은 'Stripe는 한국에서 공식 사용 불가(미국 법인 Stripe Atlas 필요, 초기 비용), 그래서 PayPal'이라고 했다.
     한국 결제는 토스페이먼츠에 문의하라고 했다. 이 도구는 그 조건을 규칙으로 옮기고 수수료는 가정값으로 비교한다.
  4) 개발: Stitch -> Export -> MCP -> API 키 -> Antigravity IDE에 Stitch MCP 설치 -> 프롬프트 복사 -> 화면 가져오기
     -> 'React로 localhost 개발' -> 고객 시점 시뮬레이션 -> 오류를 복사해 붙여 넣어 자동 디버깅. 지시문을 만들어 준다.
  5) 다음 편: 데이터베이스(누가 무엇을 샀는지)와 PayPal 결제 연결.
'(추가)'는 내가 덧붙인 점검이다. 수수료·초기 비용 숫자는 영상에 없어 가정값이다. 표준 라이브러리만 사용."""
import re

PAGES_DEFAULT = ["메인", "전자책 상세", "전자책 라이브러리", "구매 완료·다운로드"]
HEX = re.compile(r"^#?([0-9a-fA-F]{6})$")


def _num(v, default, lo=0.0):
    try:
        x = float(str(v).replace(",", "").strip())
    except (TypeError, ValueError):
        return default
    return x if x >= lo else default


def _yn(v):
    return str(v or "").strip().lower() in ("y", "yes", "예", "네", "true", "1")


def _split(s):
    return [x.strip() for x in str(s or "").replace("\n", ",").split(",") if x.strip()]


def _rgb(h):
    m = HEX.match(str(h).strip())
    if not m:
        return None
    v = m.group(1)
    return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))


def _lum(rgb):
    def ch(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(fg, bg):
    """WCAG 대비비(1~21). 색 형식이 틀리면 None."""
    a, b = _rgb(fg), _rgb(bg)
    if a is None or b is None:
        return None
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def design_md(brand, audience, tone, primary, bg, text, font, button):
    """영상 3:38 'Design.md': 디자인 작업 매뉴얼을 AI에 넣는 문서. 색 대비를 계산해 경고한다."""
    warns = []
    for name, fg, b in (("본문 글자/배경", text, bg), ("버튼 글자(흰색)/주색", "#ffffff", primary)):
        c = contrast(fg, b)
        if c is None:
            warns.append("%s: 색 형식이 틀렸다(#RRGGBB)" % name)
        elif c < 4.5:
            warns.append("%s 대비 %.2f:1 — 4.5:1 미만이라 읽기 어렵다(WCAG AA 기준, 추가 점검)" % (name, c))
    c1 = contrast(text, bg)
    c2 = contrast("#ffffff", primary)
    lines = [
        "# Design.md — %s" % (brand or "(브랜드명)"),
        "",
        "## 대상과 분위기",
        "- 대상: %s" % (audience or "(대상 고객)"),
        "- 분위기: %s" % (tone or "(예: 신뢰감 있고 따뜻한)"),
        "",
        "## 색",
        "- 주색(버튼·강조): %s" % primary,
        "- 배경: %s / 본문 글자: %s" % (bg, text),
        "- 본문 대비비: %s, 버튼 글자 대비비: %s" % (("%.2f:1" % c1) if c1 else "계산 불가", ("%.2f:1" % c2) if c2 else "계산 불가"),
        "",
        "## 글꼴",
        "- 기본 글꼴: %s (제목은 굵게, 본문은 16px 이상)" % (font or "Pretendard"),
        "",
        "## 버튼",
        "- 모양: %s. 한 화면에 주 버튼은 1개만." % (button or "둥근 모서리"),
        "",
        "## 규칙(모든 페이지에 똑같이 적용)",
        "- 모든 페이지는 이 색·글꼴·버튼 규칙만 쓴다. 새 색을 임의로 만들지 않는다.",
        "- 모바일 먼저(폭 360px에서도 가로 스크롤이 없어야 한다)(추가).",
    ]
    return "\n".join(lines), warns


def page_prompts(brand, product, pages, design_ref="위 Design.md"):
    """영상 4:24~6:55: 사이트 프롬프트와 여러 페이지. 페이지마다 목적·필수 요소를 붙인다."""
    purpose = {
        "메인": "방문자가 5초 안에 무엇을 파는지 알게 한다. 대표 문구, 핵심 혜택 3개, 시작 버튼.",
        "상세": "구매 결정을 돕는다. 누가 썼는지, 무엇을 배우는지, 목차, 후기, 가격, 구매 버튼.",
        "라이브러리": "어떤 전자책이 있는지 한눈에 본다. 목록, 검색, 표지 카드.",
        "결제": "이름 입력, 카드 또는 PayPal 선택, 구매 완료, 다운로드 버튼. 가상화폐 결제는 넣지 않는다.",
        "다운로드": "구매 완료 안내와 다운로드 버튼, 영수증 안내.",
    }
    out = []
    for i, pg in enumerate(pages, 1):
        alias = (("메인", "메인"), ("상세", "상세"), ("라이브러리", "라이브러리"), ("결제", "결제"), ("구매", "결제"), ("다운로드", "다운로드"))
        key = next((v for k, v in alias if k in pg), None)
        out.append("[페이지 %d: %s]" % (i, pg))
        out.append("%s 의 '%s' 페이지를 디자인해 줘. %s 를 따른다." % (brand or "(브랜드)", pg, design_ref))
        out.append("상품: %s. 목적: %s" % (product or "(상품)", purpose.get(key, "이 페이지의 목적을 한 문장으로 적어 주세요.")))
        out.append("다른 페이지와 헤더·푸터·버튼 모양을 똑같이 맞춘다.")
        out.append("")
    return "\n".join(out).rstrip()


def payment_compare(price, sales, providers, sell_global, setup_months=12):
    """영상 8:40 결제 수단. providers: dict 목록(name,pct,fixed,setup,korea_direct,region). 모두 가정값.
    규칙(영상): Stripe는 한국에서 공식 사용 불가(미국 법인 필요, 초기 비용) / 토스는 한국 결제용 / PayPal은 바로 시작."""
    rows = []
    for d in providers:
        fee = price * d["pct"] / 100.0 + d["fixed"]
        net = price - fee
        month = net * sales
        status, month_eff = "바로 사용", month
        if sell_global and d["region"] == "한국":
            status, month_eff = "불가(해외 고객 결제 안 됨)", None
        elif not d["korea_direct"]:
            status = "조건부(미국 법인 등 준비 필요, 초기비용 %s원을 %d개월로 나눠 반영)" % (format(int(d["setup"]), ","), setup_months)
            month_eff = month - d["setup"] / float(setup_months)
        rows.append({"name": d["name"], "fee": fee, "net": net, "month": month, "month_eff": month_eff, "status": status})
    ok = sorted([r for r in rows if r["month_eff"] is not None], key=lambda r: r["month_eff"], reverse=True)
    bad = [r for r in rows if r["month_eff"] is None]
    return ok, bad


def redesign_prompt(change):
    """영상 3:38 직후: Design.md 수정은 Gemini에게 시킨다."""
    return ("아래 Design.md 내용을 수정해 줘. 요청: %s\n전체 파일을 다시 써 주고, 색은 #RRGGBB 로 적어 줘.\n(여기에 Design.md 전체를 붙여 넣기)"
            % (change or "배경은 흰색, 눈에 잘 띄게"))


def dev_prompts(site_name):
    """영상 15:34~22:00: Antigravity에서 쓰는 지시문 3개."""
    return [
        "1) 가져오기: (Stitch에서 Export → MCP → Copy Prompt 로 복사한 문장을 그대로 붙여 넣는다). 그 전에 설정 → MCP 서버에 Stitch가 설치·활성화되어 있어야 한다.",
        "2) 개발: 이 웹사이트(%s)를 React로 개발해 줘. localhost 에서 볼 수 있게 시작해 줘. 계획을 먼저 보여 주고, 설치 후 npm run build 로 확인해 줘." % (site_name or "(사이트 이름)"),
        "3) 시뮬레이션: 전자책 선택 → 상세 → 결제 페이지까지 고객이 되어 따라가며 보이게 시뮬레이션해 줘. 필요한 기능 설계도 가져와 줘.",
        "4) 오류가 나면: 화면의 오류 문구를 전부 복사해 그대로 붙여 넣는다(영상: 자동으로 원인을 찾아 고친다). 글자가 아이콘 대신 글자로만 보이면 '모든 화면을 보고 고쳐 줘'라고 말한다.",
        "5) 한국어 설명이 필요하면: 앞으로 한국어로 설명해 줘.",
    ]


SETUP = [
    ("2:25", "stitch.withgoogle.com 에서 Stitch 2.0 열기. '디자인으로 시작'에서 .md 파일을 올리면 사이트를 만든다", None),
    ("3:38", "Design.md(색·글꼴·버튼 모서리)와 로고를 올리고, 앱이 아닌 '웹사이트'를 고른다. 모델은 3.1을 고르면 더 오래 생각한다", None),
    ("4:24", "만들고 싶은 사이트를 한 문장으로 적고 '메인 페이지 만들어' 지시", None),
    ("6:55", "'여러 페이지 만들어' → 상세·라이브러리·구매 완료·다운로드. AI가 구성을 되묻는다 → 확인", None),
    ("8:40", "해외 고객이면 PayPal, 한국 결제는 토스페이먼츠. 가상화폐는 빼고 카드+PayPal만 남긴다", "추가: 정산 통화·수수료는 공식 요금표로 확인"),
    ("9:58", "색을 바꾸려면 오른쪽 design.md 에서 색을 고르고 '저장 및 적용'. 되돌리려면 원래 색 코드를 다시 입력", "추가: 바꾼 뒤 대비비를 다시 계산"),
    ("11:45", "모든 화면 선택 → 오른쪽 위 점 3개 → Export → MCP → Setup MCP → API 키 → IDE로 Antigravity 선택", "추가: API 키는 코드·저장소에 넣지 말고 IDE 설정에만 둔다"),
    ("14:09", "Antigravity IDE(2.0 아님) 설치 → 점 3개 → MCP 서버 → 'Stitch' 설치 → API 키 붙여 넣고 저장 → 활성화", None),
    ("15:34", "새 폴더(사이트 이름) 열기 → Export → MCP → Copy Prompt 를 붙여 넣기 → 화면·코드가 'Stitch Screens' 폴더로 들어온다", None),
    ("19:00", "'React로 개발해서 localhost 로 보게 해 줘' → 계획 확인 → 실행(npm run build 확인)", None),
    ("20:20", "(선택) 터미널에서 Claude Code 켜기 — 코딩에는 쓰되 유료라 전부 맡기지는 않는다", None),
    ("22:00", "고객 시점 시뮬레이션 → 오류 복사·붙여 넣기로 자동 디버깅 → 불편한 점을 계속 고친다", None),
    ("26:08", "다음 편: 데이터베이스(누가 무엇을 샀는지)와 PayPal 결제 연결", None),
]

QA = [
    "첫 화면에서 5초 안에 무엇을 파는지 보이는가",
    "메인 → 상세 → 결제 → 다운로드 흐름이 버튼 한 번씩으로 이어지는가(영상 시뮬레이션 순서)",
    "전자책 가격·저자·후기가 상세에 보이는가(영상: '얼마지? 누가 썼지? 후기는?')",
    "모든 페이지의 헤더·푸터·버튼 모양과 색이 같은가",
    "화살표 같은 아이콘이 글자로만 나오지 않는가(영상 22:00 지적 사례)",
    "결제 화면에 가상화폐가 남아 있지 않고 금액·환불 안내가 보이는가",
    "폭 360px 폰 화면에서 가로 스크롤이 없는가(추가)",
    "본문 글자와 배경 대비비가 4.5:1 이상인가(추가)",
    "존재하지 않는 주소를 열면 안내 화면이 나오는가(추가)",
]


def api(params):
    p = params or {}
    brand = str(p.get("brand", "")).strip()
    primary = str(p.get("primary", "#2563eb")).strip()
    bg = str(p.get("bg", "#ffffff")).strip()
    text = str(p.get("text", "#111827")).strip()
    for k, v in (("주색", primary), ("배경색", bg), ("글자색", text)):
        if _rgb(v) is None:
            return {"ok": False, "text": "%s 은 #RRGGBB 형식(예: #2563eb)으로 적어 주세요." % k}
    md, warns = design_md(brand, str(p.get("audience", "")).strip(), str(p.get("tone", "")).strip(), primary, bg, text,
                          str(p.get("font", "")).strip(), str(p.get("button", "")).strip())
    pages = _split(p.get("pages", "")) or PAGES_DEFAULT
    out = ["■ 1. Design.md (영상 3:38) — Stitch에 먼저 넣는다", md]
    if warns:
        out.append("경고: " + " / ".join(warns))
    out.append("\n■ 2. 페이지별 프롬프트 (영상 4:24~6:55)")
    out.append(page_prompts(brand, str(p.get("product", "")).strip(), pages))

    price = _num(p.get("price", 19900), 19900)
    sales = _num(p.get("sales", 30), 30)
    sell_global = _yn(p.get("sell_global", "Y"))
    provs = [
        {"name": "PayPal", "pct": _num(p.get("paypal_pct", 4.0), 4.0), "fixed": _num(p.get("paypal_fixed", 500), 500), "setup": 0, "korea_direct": True, "region": "해외"},
        {"name": "Stripe", "pct": _num(p.get("stripe_pct", 3.5), 3.5), "fixed": _num(p.get("stripe_fixed", 300), 300),
         "setup": _num(p.get("atlas_setup", 700000), 700000), "korea_direct": False, "region": "해외"},
        {"name": "토스페이먼츠", "pct": _num(p.get("toss_pct", 3.0), 3.0), "fixed": _num(p.get("toss_fixed", 0), 0), "setup": 0, "korea_direct": True, "region": "한국"},
    ]
    ok, bad = payment_compare(price, sales, provs, sell_global)
    out.append("\n■ 3. 결제 수단 비교 (영상 8:40) — 수수료·초기비용은 가정값, 공식 자료로 바꿀 것")
    out.append("  전자책 %s원, 월 %d건, 해외 고객 %s" % (format(int(price), ","), int(sales), "있음" if sell_global else "없음"))
    for i, r in enumerate(ok, 1):
        out.append("  %d위 %s: 건당 수수료 %s원, 건당 실수령 %s원, 월 실수령 %s원 [%s]" % (
            i, r["name"], format(round(r["fee"]), ","), format(round(r["net"]), ","), format(round(r["month_eff"]), ","), r["status"]))
    for r in bad:
        out.append("  제외 %s: %s" % (r["name"], r["status"]))
    out.append("  영상의 결론: Stripe는 한국에서 공식 사용이 안 되고 미국 법인(Stripe Atlas)이 필요해 초기 비용이 든다 → PayPal로 시작. 한국 결제는 토스페이먼츠에 문의.")
    out.append("\n■ 3-1. Design.md 수정 요청문(영상 3:38 직후, Gemini에게)")
    out.append(redesign_prompt(str(p.get("change", "")).strip()))
    out.append("\n■ 3-2. Antigravity 지시문 (영상 15:34~22:00)")
    out.extend("  " + x for x in dev_prompts(brand))
    out.append("\n■ 4. 출시 순서 체크리스트 (영상 순서)")
    for t, step, extra in SETUP:
        out.append("  [ ] %s 지점 — %s%s" % (t, step, ("  ※" + extra) if extra else ""))
    out.append("\n■ 5. 고객 시점 점검 (영상 22:00 + 추가 항목)")
    for q in QA:
        out.append("  [ ] " + q)
    return {"ok": True, "text": "\n".join(out), "warnings": warns, "payment_rank": [r["name"] for r in ok], "payment_excluded": [r["name"] for r in bad],
            "pages": pages}


if __name__ == "__main__":
    r = api({"brand": "글로벌 AI 교육", "product": "AI 1인 사업 전자책 19,900원", "audience": "AI가 처음인 직장인", "tone": "친절하고 신뢰감 있는"})
    assert r["ok"], r
    assert r["pages"] == PAGES_DEFAULT
    assert abs(contrast("#000000", "#ffffff") - 21.0) < 0.01
    assert r["payment_rank"][0] == "PayPal" and r["payment_excluded"] == ["토스페이먼츠"], (r["payment_rank"], r["payment_excluded"])
    kr = api({"sell_global": "N", "sales": "100"})
    assert kr["payment_rank"][0] == "토스페이먼츠", kr["payment_rank"]
    bad = api({"primary": "#facc15", "bg": "#ffffff", "text": "#9ca3af"})
    assert bad["ok"] and len(bad["warnings"]) == 2, bad["warnings"]
    assert not api({"primary": "red"})["ok"]
    print(r["text"])
    print("성공")
