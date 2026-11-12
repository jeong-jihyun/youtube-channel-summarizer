"""AI 브라우저 루틴 설계기 (영상 0C3nXlwaxIs, 네이버 블로그 자동 발행 입문).

영상이 알려 준 일 잘 시키는 법을 도구로 옮겼다.
  1) 육하원칙 지시문(15:11~17:37): 이름 지정 -> 목표 -> 언제 -> 어디서 -> 방법(번호 단계) ->
     공통 키워드로 사실 판단 -> 마지막 홍보 문구. 빠진 칸을 알려 준다.
  2) 발행 방식(17:37): 초안 저장 vs 자동 발행. 설명란의 주의(사실관계·저작권·이용정책 확인,
     처음엔 초안)를 점검표로 만든다.
  3) 루틴 중복(20:05): 시험하다 같은 루틴이 2개 겹쳤던 장면 -> 시각·게시처 겹침 점검.
  4) 모델 연결(6:18~9:28): 무료 크레딧 / 구독 연결 / API 키 / 로컬 AI 중 무엇이 맞는지,
     API는 월 비용을 가정값으로 계산해 월 20달러 요금제(영상 21:13)와 비교.
토큰 사용량, 단가, 환율, 사고 수준별 배율은 모두 가정값이다(영상에 수치 없음). 표준 라이브러리만 사용."""
import re

DEFAULT_STEPS = """X에서 키워드로 AI 동향을 찾는다
네이버에서 키워드로 AI 뉴스를 찾는다
구글에서 키워드로 AI 뉴스를 찾는다
1, 2, 3에 공통으로 나온 키워드를 찾아 사실인지 거짓인지 판단하고 대중에게 도움이 되게 쉽게 쓴다"""

DEFAULT_EXISTING = """08:00|블로그 자동 발행|네이버 블로그
08:00|블로그 초안 점검|네이버 블로그
09:00|사이트 최적화 점검|내 웹사이트"""

SUPPORTED_SUBS = {"chatgpt": "ChatGPT", "claude": "Claude", "grok": "Grok"}   # 영상 7:15 부근: 로그인으로 연결
UNSUPPORTED_SUBS = {"gemini": "Gemini"}   # 영상: 구글은 제휴가 안 된 듯 -> 구독 동기화 안 됨, API 키로
EFFORT = {"낮음": 0.6, "중간": 1.0, "높음": 1.8, "최대": 3.0}   # 가정: 사고 수준별 토큰 배율


def _num(v, default, lo=0):
    try:
        x = float(str(v).replace(",", "").strip())
    except (TypeError, ValueError):
        return default
    return x if x >= lo else default


def _split(s):
    return [x.strip() for x in str(s or "").replace("\n", ",").split(",") if x.strip()]


def _lines(s):
    return [x.strip() for x in str(s or "").splitlines() if x.strip()]


def _hhmm(s):
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", str(s).strip())
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2))
    return h * 60 + mi if h < 24 and mi < 60 else None


def build_instruction(a):
    """붙여 넣을 지시문과 빠진 칸 목록을 돌려준다."""
    out, gaps = [], []
    if a["name"]:
        out.append("너의 이름: %s. 지금부터 나를 위해 일하는 웹 전용 AI 직원이다." % a["name"])
    else:
        gaps.append("누가: AI 직원 이름을 정하지 않았다(영상은 'Brown'이라는 이름을 붙였다)")
    if a["goal"]:
        out.append("목표: " + a["goal"])
    else:
        gaps.append("왜/무엇을: 목표가 비어 있다")
    if a["when"]:
        out.append("언제: " + a["when"])
    else:
        gaps.append("언제: 시각이 없다")
    if a["where"]:
        out.append("어디서: " + ", ".join(a["where"]) + " (브라우저로 직접 들어가 확인해)")
    else:
        gaps.append("어디서: 들어갈 사이트가 없다")
    if a["steps"]:
        out.append("방법:")
        for i, s in enumerate(a["steps"], 1):
            out.append("  %d. %s" % (i, s))
    else:
        gaps.append("어떻게: 단계가 없다(영상은 번호 매긴 단계를 '매뉴얼'처럼 줬다)")
    blob = " ".join(a["steps"]) + " " + a["goal"]
    if not re.search(r"사실|확인|검증|출처", blob):
        gaps.append("사실 확인 단계가 없다(영상은 공통 키워드의 참/거짓을 판단하게 했다)")
    if a["promo"]:
        out.append("마지막에 이렇게 홍보해: " + a["promo"])
    out.append("저장 방식: " + ("초안으로만 저장하고 발행하지 마. 내가 확인한 뒤 직접 발행할게."
                              if a["mode"] == "초안" else "작성이 끝나면 확인 없이 바로 자동 발행해."))
    if a["steps"] and len(a["steps"]) < 2:
        gaps.append("단계가 1개뿐이다. 찾기/비교/작성처럼 나누면 AI가 따라가기 쉽다")
    if a["where"] and a["steps"]:
        for w in a["where"][:-1]:
            if not any(w in s for s in a["steps"]):
                gaps.append("어디서에 쓴 '%s'가 방법 단계에 한 번도 나오지 않는다" % w)
    return out, gaps


def check_conflicts(new, existing):
    """같은 시각, 또는 같은 게시처에서 60분 안에 겹치는 루틴."""
    res = []
    for e in existing:
        if new["time"] is None or e["time"] is None:
            continue
        gap = abs(new["time"] - e["time"])
        same_target = new["target"] and new["target"] == e["target"]
        if gap == 0 and same_target:
            res.append("같은 시각·같은 게시처 겹침: '%s' (영상에서 시험하다 루틴이 중복되어 하나를 지웠다)" % e["name"])
        elif gap == 0:
            res.append("같은 시각에 다른 루틴이 있음: '%s' (동시에 돌면 느려지거나 충돌할 수 있다)" % e["name"])
        elif same_target and gap <= 60:
            res.append("같은 게시처에서 %d분 간격: '%s' (글이 이중으로 올라갈 수 있다)" % (gap, e["name"]))
    dups = {}
    for e in existing:
        key = (e["time"], e["target"])
        dups.setdefault(key, []).append(e["name"])
    for (t, tg), names in dups.items():
        if len(names) > 1 and t is not None:
            res.append("기존 목록 안에서 이미 겹침: " + " / ".join(names))
    return res


def model_options(a):
    subs = [s.lower() for s in a["subs"]]
    ok = [SUPPORTED_SUBS[s] for s in subs if s in SUPPORTED_SUBS]
    no = [UNSUPPORTED_SUBS[s] for s in subs if s in UNSUPPORTED_SUBS]
    runs = a["runs"]
    tokens = a["tokens"] * EFFORT[a["effort"]]
    usd = runs * tokens / 1e6 * a["price"]
    krw = usd * a["krw"]
    L = []
    L.append("  - 무료 크레딧: 영상은 약 500 크레딧을 준다고 했다. 1회 실행에 몇 크레딧이 드는지는 영상에 없어 계산하지 않았다(직접 1회 돌려 보고 줄어든 양을 확인).")
    if ok:
        L.append("  - 구독 연결: %s 구독이 있으면 로그인으로 연결(영상 시연). 추가 요금 없음, 한도는 구독 쪽을 따른다." % ", ".join(ok))
    else:
        L.append("  - 구독 연결: ChatGPT·Claude·Grok 구독이 없으면 해당 없음.")
    if no:
        L.append("  - %s 구독은 영상에서 연결되지 않는다고 했다 -> API 키(구글 AI Studio)를 쓴다." % ", ".join(no))
    L.append("  - API 키(쓴 만큼 지불): 월 %d회 x 실행당 %s토큰(%s 배율 %.1f) x 100만 토큰당 %g달러 = 약 %.2f달러(약 %s원, 환율 %g 가정)." % (
        runs, format(int(a["tokens"]), ","), a["effort"], EFFORT[a["effort"]], a["price"], usd, format(int(krw), ","), a["krw"]))
    if usd < 20:
        L.append("    -> 월 20달러 요금제(영상 21:13)보다 API가 %.2f달러 싸다(가정 기준)." % (20 - usd))
    else:
        L.append("    -> 월 20달러 요금제가 API보다 %.2f달러 싸다(가정 기준)." % (usd - 20))
    L.append("  - 로컬 AI: " + ("PC가 충분하다고 했으므로 LM Studio·Ollama 키를 연결할 수 있다. 단 영상은 일반 PC에는 AI 브라우저 요구량이 커서 한계가 있다고 했다."
                              if a["local_ok"] else "PC 사양이 부족하면 추천하지 않는다(영상: 일반 컴퓨터에는 요구량이 과하다)."))
    if ok:
        rec = "구독 연결(%s)로 시작" % ok[0]
    elif usd < 20:
        rec = "API 키 종량제로 시작(월 약 %.2f달러)" % usd
    else:
        rec = "월 20달러 요금제 또는 실행 횟수·사고 수준을 줄여 API 비용 절감"
    return L, rec, usd


def api(params):
    p = params or {}
    effort = str(p.get("effort", "중간")).strip()
    if effort not in EFFORT:
        return {"ok": False, "text": "사고 수준은 %s 중 하나로 입력하세요." % ", ".join(EFFORT)}
    mode = str(p.get("mode", "초안")).strip()
    if mode not in ("초안", "자동"):
        return {"ok": False, "text": "발행 방식은 '초안' 또는 '자동'입니다."}
    run_time = _hhmm(p.get("run_time", "08:00"))
    if run_time is None:
        return {"ok": False, "text": "실행 시각은 HH:MM 형식(예 08:00)으로 입력하세요."}
    where = _split(p.get("where", "X,네이버,구글,네이버 블로그"))
    a = {"name": str(p.get("name", "Brown")).strip(), "goal": str(p.get("goal", "매일 AI 뉴스를 모아 쉬운 블로그 글 1개를 쓴다")).strip(),
         "when": str(p.get("when", "매일 오전 8시(한국 시간)")).strip(), "where": where,
         "steps": _lines(p.get("steps", DEFAULT_STEPS)), "promo": str(p.get("promo", "")).strip(), "mode": mode,
         "subs": _split(p.get("subs", "claude")), "runs": int(_num(p.get("runs"), 30, 0)), "tokens": _num(p.get("tokens"), 150000, 0),
         "price": _num(p.get("price"), 5.0, 0), "krw": _num(p.get("krw"), 1400, 1), "effort": effort,
         "local_ok": str(p.get("local_ok", "N")).strip().upper() == "Y"}
    ins, gaps = build_instruction(a)
    L = ["[1] AI 브라우저 채팅에 붙여 넣을 지시문 (육하원칙: 누가·언제·어디서·어떻게·왜)"]
    L += ["  " + x for x in ins]
    L.append("  빠진 칸: " + ("없음" if not gaps else ""))
    L += ["   - " + g for g in gaps]
    L.append("")
    L.append("[2] 발행 방식 점검 (%s)" % ("초안 저장: 사람이 확인한 뒤 발행. 처음에 가장 안전" if mode == "초안" else "자동 발행: 확인 없이 올라간다"))
    if mode == "자동":
        L.append("   ! 영상 설명란 주의: 사실관계·저작권·사이트 이용정책을 확인한 뒤 발행하세요. 처음 며칠은 초안으로 시험하는 것을 권장합니다.")
        L.append("   ! 자동 실행에는 실행 환경, 로그인 상태, 권한이 필요합니다(PC가 꺼지면 안 돌 수 있다).")
        L.append("   ! 자동화가 수익이나 검색 노출을 보장하지 않습니다.")
    else:
        L.append("   - 초안 5건 정도를 직접 읽어 보고 사실 오류가 없을 때 자동 발행으로 바꾸세요(내가 정한 권장).")
    L.append("")
    existing = []
    for ln in _lines(p.get("existing", DEFAULT_EXISTING)):
        c = [x.strip() for x in ln.split("|")]
        if len(c) == 3:
            existing.append({"time": _hhmm(c[0]), "name": c[1], "target": c[2]})
    new = {"time": run_time, "target": where[-1] if where else "", "name": "새 루틴"}
    conf = check_conflicts(new, existing)
    L.append("[3] 루틴 겹침 점검 (새 루틴 %02d:%02d, 게시처 %s, 기존 %d개)" % (run_time // 60, run_time % 60, new["target"] or "미입력", len(existing)))
    L += ["   ! " + c for c in conf] if conf else ["   - 겹치는 루틴 없음"]
    L.append("")
    opts, rec, usd = model_options(a)
    L.append("[4] 모델 연결 선택 (영상 6:18~9:28, 사고 수준 '%s': 블로그 글은 중간이면 충분하다고 했다)" % effort)
    L += opts
    L.append("  => 추천: " + rec + ". 토큰·단가·환율은 가정값이니 실제 청구서로 바꿔 넣으세요.")
    return {"ok": True, "text": "\n".join(L), "gaps": gaps, "conflicts": conf, "api_usd": round(usd, 2), "recommend": rec}


if __name__ == "__main__":
    r = api({"promo": "CONNECT AI LAB 유튜브 구독"})
    assert r["ok"], r
    assert "[4]" in r["text"] and r["conflicts"], r
    assert api({"effort": "x"})["ok"] is False
    print(r["text"])
    print("성공")
