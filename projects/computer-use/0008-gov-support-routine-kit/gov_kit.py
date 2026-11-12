"""정부지원사업 AI 직원 루틴 키트 (영상 rheqwcrTxV4, AI 야학당).

영상이 보여 준 '정부과제를 AI 에이전트에게 맡기는 방법'을 입력만 넣으면 쓸 수 있게 옮겼다.
  1) 프롬프트 구성(영상 9:17~11:19): 찾을 지원 종류 + 확인할 출처 + 공식 공고 확인 + 내 사업 정보
  2) 지원 종류 3가지(사무/인건비/대출) 중 내게 맞는 것, 업력·지역·대상 조건으로 공고 걸러 내기
  3) 접수 서류 5종(사업자등록증, 국세 완납, 지방세 완납, 등기부, 대표 경력) 준비 점검
  4) 사람이 해야 하는 일(본인인증, 서류 발급, 최종 확인)
  5) 시간대별 루틴표(10시 정부과제, 11시 이메일, 12시 유튜브 스튜디오 예) + 겹침 점검
  6) 보안 수준(영상 14:07): 걱정되면 정보를 적게 준다 -> 프롬프트에 넣을 정보를 3단계로 조절
공고 적합도 점수·임박 기준(3일)은 영상 내용이 아니라 내가 정한 경험칙이다.
표준 라이브러리만 사용, 외부 호출 없음. 실제 공고를 가져오지 않고 사용자가 붙여 넣은 공고만 판정한다."""
import datetime

DEFAULT_NOTICES = """청년 창업 사무공간 지원|사무|2026-12-05|3|인천|1500|전체
초기 창업 인건비 지원|인건비|2026-11-14|7|전국|3000|법인
창업 운영자금 저금리 대출|대출|2026-12-31|없음|전국|10000|전체
예비창업자 패키지|사무|2026-11-30|0|전국|5000|예비
부산 소상공인 공간 임대|사무|2026-12-10|5|부산|800|개인
지난 마감 공고 예시|인건비|2026-10-31|7|전국|2000|전체"""

DEFAULT_ROUTINES = """10:00|정부과제 공고 탐색
11:00|이메일에서 구독료·결제 점검
12:00|유튜브 스튜디오 댓글·이탈 분석"""

DOCS = [
    ("사업자등록증", "개인·법인 공통", "본인인증이 필요한 발급이 많다"),
    ("국세 완납증명", "공통", "세금 완납 상태여야 발급된다"),
    ("지방세 완납증명", "공통", "세금 완납 상태여야 발급된다"),
    ("등기부등본", "법인", "개인사업자·예비창업자는 공고가 요구하는 대체 서류를 확인"),
    ("대표자 경력 자료", "공통", "영상에서는 '경력 15년 차 AI 연구자' 소개를 넣었다"),
]
KINDS = ("사무", "인건비", "대출")
TYPES = ("개인", "법인", "예비", "재창업")


def _date(s):
    return datetime.date.fromisoformat(str(s).strip())


def _num(v):
    try:
        return float(str(v).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _split(s):
    return [x.strip() for x in str(s or "").replace("\n", ",").split(",") if x.strip()]


def years_since(founded, today):
    return max(0.0, (today - founded).days / 365.25)


def parse_notices(text):
    items, bad = [], []
    for raw in str(text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        c = [x.strip() for x in line.split("|")]
        if len(c) < 7:
            bad.append(line)
            continue
        try:
            dl = _date(c[2])
        except ValueError:
            bad.append(line)
            continue
        mx = None if c[3] in ("없음", "") else _num(c[3])
        if c[3] not in ("없음", "") and mx is None:
            bad.append(line)
            continue
        items.append({"title": c[0], "kind": c[1], "deadline": dl, "max_years": mx, "region": c[4],
                      "amount": _num(c[5]) or 0.0, "target": c[6]})
    return items, bad


def evaluate(n, prof):
    """공고 1개를 내 사업 정보와 비교한다. verdict: 후보 / 보류 / 제외."""
    why, flags, score = [], [], 0
    dday = (n["deadline"] - prof["today"]).days
    if dday < 0:
        return {"n": n, "verdict": "제외", "why": ["마감 지남"], "flags": [], "score": 0, "dday": dday}
    if n["target"] != "전체" and n["target"] != prof["biz_type"]:
        return {"n": n, "verdict": "제외", "why": ["대상이 다름(공고: %s, 나: %s)" % (n["target"], prof["biz_type"])],
                "flags": [], "score": 0, "dday": dday}
    reg = n["region"]
    if reg == "전국":
        score += 1
    elif prof["region"] and (reg in prof["region"] or prof["region"] in reg):
        score += 2
        why.append("지역 일치")
    else:
        return {"n": n, "verdict": "제외", "why": ["지역이 다름(공고: %s)" % reg], "flags": [], "score": 0, "dday": dday}
    if n["max_years"] is None:
        flags.append("업력 조건을 공고 원문에서 확인")
    elif prof["biz_type"] == "예비" or prof["years"] <= n["max_years"]:
        score += 1
        why.append("업력 %.1f년 <= 한도 %g년" % (prof["years"], n["max_years"]))
    else:
        return {"n": n, "verdict": "제외", "why": ["업력 %.1f년이 한도 %g년 초과" % (prof["years"], n["max_years"])],
                "flags": [], "score": 0, "dday": dday}
    if n["kind"] in prof["want"]:
        score += 3
        why.append("원하는 종류(%s)" % n["kind"])
    else:
        flags.append("원하는 종류가 아님(%s)" % n["kind"])
    if dday <= 3:
        flags.append("마감 임박(D-%d)" % dday)
    verdict = "후보" if score >= 4 and not any("확인" in f for f in flags) else "보류"
    return {"n": n, "verdict": verdict, "why": why, "flags": flags, "score": score, "dday": dday}


def build_prompt(prof, level):
    """level: 최소 / 보통 / 상세. 영상 9:17~11:19 구성 + 14:07 보안 조언."""
    lines = []
    lines.append("내가 해 볼 만한 %s 지원사업(창업 지원·사업 지원)을 찾아 줘." % "·".join(prof["want"]))
    lines.append("확인할 곳: %s. 주관 기관과 공식 공고 원문도 확인해." % ", ".join(prof["sources"]))
    if level == "최소":
        lines.append("내 정보는 아직 주지 않을 거야. 조건을 물어보고 일반적인 지원 종류부터 정리해 줘.")
    else:
        info = ["사업자 형태: %s" % prof["biz_type"]]
        if prof["industry"]:
            info.append("하는 일: %s" % prof["industry"])
        info.append("지역: %s" % prof["region"] if prof["region"] else "지역: 미입력")
        if prof["founded"]:
            info.append("창업 시점: %s (업력 약 %.1f년)" % (prof["founded"].isoformat(), prof["years"]))
        if level == "상세" and prof["age"]:
            info.append("대표 나이: %d세" % prof["age"])
        lines.append("내 정보 -> " + " / ".join(info))
    lines.append("조건이 맞는 공고만 골라 마감일, 지원 대상, 지원 금액, 필요 서류를 표로 정리해.")
    lines.append("본인인증, 서류 발급, 최종 제출 전에는 반드시 멈추고 나에게 물어봐. 비밀번호는 네가 저장하지 마.")
    return lines


def api(params):
    p = params or {}
    try:
        today = _date(p.get("today", "2026-11-12"))
    except ValueError:
        return {"ok": False, "text": "기준일은 YYYY-MM-DD 형식으로 입력하세요."}
    biz = str(p.get("biz_type", "법인")).strip()
    if biz not in TYPES:
        return {"ok": False, "text": "사업자 형태는 %s 중 하나로 입력하세요." % ", ".join(TYPES)}
    fstr = str(p.get("founded", "2025-12-15")).strip()
    founded = None
    if fstr and fstr != "없음":
        try:
            founded = _date(fstr)
        except ValueError:
            return {"ok": False, "text": "창업 시점은 YYYY-MM-DD 또는 '없음'으로 입력하세요."}
        if founded > today:
            return {"ok": False, "text": "창업 시점이 기준일보다 뒤입니다."}
    if founded is None and biz != "예비":
        return {"ok": False, "text": "예비창업자가 아니면 창업 시점(YYYY-MM-DD)이 필요합니다."}
    want = [w for w in _split(p.get("want", "사무,인건비,대출")) if w in KINDS]
    if not want:
        return {"ok": False, "text": "원하는 지원 종류는 %s 중에서 골라 쉼표로 쓰세요." % ", ".join(KINDS)}
    level = str(p.get("level", "보통")).strip()
    if level not in ("최소", "보통", "상세"):
        return {"ok": False, "text": "정보 공개 수준은 최소, 보통, 상세 중 하나입니다."}
    age = _num(p.get("age"))
    prof = {"today": today, "biz_type": biz, "region": str(p.get("region", "")).strip(),
            "industry": str(p.get("industry", "")).strip(), "founded": founded,
            "years": years_since(founded, today) if founded else 0.0, "want": want,
            "sources": _split(p.get("sources", "정부24,K-스타트업,기업마당")) or ["정부24", "K-스타트업", "기업마당"],
            "age": int(age) if age else 0}
    notices, bad = parse_notices(p.get("notices", DEFAULT_NOTICES))
    ready = set(_split(p.get("docs_ready", "")))
    L = ["[1] AI 비서에게 붙여 넣을 프롬프트 (정보 공개 수준: %s)" % level]
    L += ["  " + x for x in build_prompt(prof, level)]
    L.append("")
    L.append("[2] 붙여 넣은 공고 판정 (기준일 %s, 내 형태 %s, 업력 %.1f년, 지역 %s, 원하는 종류 %s)" % (
        today.isoformat(), biz, prof["years"], prof["region"] or "미입력", "/".join(want)))
    res = [evaluate(n, prof) for n in notices]
    order = {"후보": 0, "보류": 1, "제외": 2}
    res.sort(key=lambda r: (order[r["verdict"]], r["dday"] if r["dday"] >= 0 else 9999, -r["n"]["amount"]))
    for r in res:
        n = r["n"]
        L.append("  [%s] %s (%s, %s만원, 마감 %s%s)%s%s" % (
            r["verdict"], n["title"], n["kind"], format(int(n["amount"]), ","), n["deadline"].isoformat(),
            "" if r["dday"] < 0 else ", D-%d" % r["dday"],
            " | " + ", ".join(r["why"]) if r["why"] else "", " | 주의: " + ", ".join(r["flags"]) if r["flags"] else ""))
    if not res:
        L.append("  붙여 넣은 공고가 없습니다. (한 줄: 제목|종류|마감일|최대업력(년 또는 없음)|지역|지원금(만원)|대상)")
    if bad:
        L.append("  읽지 못한 줄: " + "; ".join(bad))
    cands = [r for r in res if r["verdict"] == "후보"]
    L.append("  -> 후보 %d개, 보류 %d개, 제외 %d개. 점수·판정 기준은 내가 정한 경험칙이며 지원 자격은 공고 원문이 우선입니다." % (
        len(cands), sum(1 for r in res if r["verdict"] == "보류"), sum(1 for r in res if r["verdict"] == "제외")))
    L.append("")
    L.append("[3] 접수 서류 5종 점검 (영상: 사업자등록증, 국세 완납, 지방세 완납, 등기부, 경력으로 서류를 만들어 메일 접수)")
    miss = 0
    for name, scope, note in DOCS:
        if scope == "법인" and biz != "법인":
            st = "해당 여부 확인"
        elif name in ready:
            st = "준비됨"
        else:
            st = "필요"
            miss += 1
        L.append("  [%s] %s - %s" % (st, name, note))
    L.append("  -> 아직 필요한 서류 %d종. 서류 발급은 사람이 직접 합니다(발급 사이트는 공고 안내를 따르세요)." % miss)
    L.append("")
    L.append("[4] 사람이 꼭 해야 하는 일 (영상 챕터 '사람이 꼭 해야 하는 부분')")
    L.append("  1) 본인인증  2) 서류 발급  3) 제출 전 최종 확인 - AI 초안의 금액·날짜·사업 설명을 눈으로 확인")
    L.append("")
    rs = []
    for raw in str(p.get("routines", DEFAULT_ROUTINES)).splitlines():
        c = [x.strip() for x in raw.split("|")]
        if len(c) == 2 and len(c[0]) == 5 and c[0][2] == ":" and c[0][:2].isdigit() and c[0][3:].isdigit():
            rs.append((c[0], c[1]))
    L.append("[5] 하루 루틴표 (영상 11:50~17:35: 루틴 = 시각을 정해 매일 반복)")
    seen = {}
    for t, name in sorted(rs):
        dup = " <- 같은 시각 겹침" if t in seen else ""
        seen[t] = name
        L.append("  %s  %s%s" % (t, name, dup))
    if not rs:
        L.append("  입력한 루틴이 없습니다. (한 줄: HH:MM|할 일)")
    L.append("  -> 처음 1주는 '찾아서 알려 줘'까지만 시키고, 문서 작성·지원은 결과를 본 뒤 맡기세요(내가 정한 권장).")
    text = "\n".join(L)
    return {"ok": True, "text": text, "candidates": [r["n"]["title"] for r in cands], "missing_docs": miss,
            "years": round(prof["years"], 2)}


if __name__ == "__main__":
    r = api({"region": "인천", "industry": "AI 서비스"})
    assert r["ok"], r
    assert "[1]" in r["text"] and "[5]" in r["text"]
    assert r["candidates"], r
    assert api({"today": "x"})["ok"] is False
    print(r["text"])
    print("성공")
