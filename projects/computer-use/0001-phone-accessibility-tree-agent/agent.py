"""모의 스마트폰 유즈: 접근성 트리(JSON)를 읽고 다음 행동을 고르는 작은 에이전트.
실제 폰/계정/API 키를 쓰지 않고, 파이썬 안의 가짜 폰 상태로만 동작한다."""
import json

# --- 가짜 폰: 화면마다 접근성 트리(JSON)를 돌려준다 ---------------------------
class FakePhone:
    def __init__(self):
        self.screen = "home"
        self.draft = ""
        self.posts = []

    def tree(self):
        if self.screen == "home":
            nodes = [{"id": "app_threads", "role": "button", "label": "Threads"},
                     {"id": "app_coupang", "role": "button", "label": "Coupang"}]
        elif self.screen == "threads":
            nodes = [{"id": "btn_plus", "role": "button", "label": "새 글"},
                     {"id": "feed", "role": "list", "label": f"내 글 {len(self.posts)}개"}]
        elif self.screen == "compose":
            nodes = [{"id": "txt_body", "role": "textfield", "label": "내용", "value": self.draft},
                     {"id": "btn_post", "role": "button", "label": "게시"}]
        else:
            nodes = []
        return {"screen": self.screen, "nodes": nodes}

    def act(self, action):
        kind, target = action["do"], action.get("id")
        if kind == "tap" and target == "app_threads":
            self.screen = "threads"
        elif kind == "tap" and target == "btn_plus":
            self.screen = "compose"
        elif kind == "type" and target == "txt_body":
            self.draft = action["text"]
        elif kind == "tap" and target == "btn_post" and self.draft:
            self.posts.append(self.draft)
            self.draft, self.screen = "", "threads"
        else:
            raise ValueError(f"할 수 없는 행동: {action}")

# --- 에이전트: 트리를 보고 목표(글 올리기)에 맞는 행동 선택 -------------------
def choose(tree, text, done):
    ids = {n["id"]: n for n in tree["nodes"]}
    if done:
        return None
    if "app_threads" in ids:
        return {"do": "tap", "id": "app_threads"}
    if "btn_plus" in ids:
        return {"do": "tap", "id": "btn_plus"}
    if "txt_body" in ids and not ids["txt_body"].get("value"):
        return {"do": "type", "id": "txt_body", "text": text}
    if "btn_post" in ids:
        return {"do": "tap", "id": "btn_post"}
    return None

def tokens_of_tree(tree):
    return max(1, len(json.dumps(tree, ensure_ascii=False)) // 4)  # 대략 4글자=1토큰 (추정)

SCREENSHOT_TOKENS = 1500  # 스크린샷 1장의 대략적인 토큰 수 (모의 가정값)

def run(text="컴퓨터 유즈 연습 글입니다"):
    phone, steps, tree_tokens = FakePhone(), [], 0
    for _ in range(10):
        tree = phone.tree()
        tree_tokens += tokens_of_tree(tree)
        act = choose(tree, text, done=bool(phone.posts))
        if act is None:
            break
        phone.act(act)
        steps.append(act)
    return phone, steps, tree_tokens


def api(params=None):
    """웹/다른 파이썬 코드에서 부르는 진입점. params: {"text": "올릴 글"}"""
    text = (params or {}).get("text") or "컴퓨터 유즈 연습 글입니다"
    phone, steps, tt = run(text)
    return {"ok": phone.posts == [text], "posts": phone.posts, "steps": steps,
            "tree_tokens_estimate": tt, "screenshot_tokens_assumed": SCREENSHOT_TOKENS * (len(steps) + 1)}

if __name__ == "__main__":
    phone, steps, tt = run()
    for i, s in enumerate(steps, 1):
        print(i, json.dumps(s, ensure_ascii=False))
    print("올라간 글:", phone.posts)
    print(f"접근성 트리 방식 토큰(추정): {tt} / 스크린샷 방식(가정): {SCREENSHOT_TOKENS * (len(steps) + 1)}")
    assert phone.posts == ["컴퓨터 유즈 연습 글입니다"]
    print("성공")
