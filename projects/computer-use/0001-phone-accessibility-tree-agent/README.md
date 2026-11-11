# 0001 모의 스마트폰 유즈 에이전트

## 어느 영상에서 왔나
- 제목: AI에게 내 스마트폰을 맡겼습니다, 컴퓨터 유즈 말고 스마트폰 유즈 | THE FOUNDER EP.2
- 주소: https://www.youtube.com/watch?v=K4QdeGqTSfQ
- 요약: [summaries/K4QdeGqTSfQ.md](../../../summaries/K4QdeGqTSfQ.md)

## 무엇을 하나
가짜 스마트폰의 화면을 접근성 트리(JSON)로 읽고, "Threads에 글 올리기" 목표에 맞는 행동(누르기·입력)을 골라 실행한다. 실제 폰·계정·키는 쓰지 않는다. 마지막에 트리 방식과 스크린샷 방식의 토큰 수를 어림 비교한다(스크린샷 1500토큰은 가정값).

## 실행 방법
```
python3 agent.py
```

## 직접 실행한 결과 (2026-11-12)
```
1 {"do": "tap", "id": "app_threads"}
2 {"do": "tap", "id": "btn_plus"}
3 {"do": "type", "id": "txt_body", "text": "컴퓨터 유즈 연습 글입니다"}
4 {"do": "tap", "id": "btn_post"}
올라간 글: ['컴퓨터 유즈 연습 글입니다']
접근성 트리 방식 토큰(추정): 185 / 스크린샷 방식(가정): 7500
성공
```

상태: **동작 확인** — 4단계로 글이 올라가고 내부 검사(assert)가 통과했다.

<!-- standard:begin -->
## 이렇게 활용할 수 있어요
- 실제 폰·컴퓨터 유즈 에이전트를 만들기 전에 '화면을 JSON으로 읽고 → 다음 행동을 고르는' 규칙을 안전하게 연습하고 시험한다(가짜 폰이라 계정·결제 위험이 없다).
- 에이전트 규칙을 고칠 때마다 같은 시나리오로 다시 돌려 망가지지 않았는지 확인하는 회귀 시험 틀로 쓴다.
- 접근성 트리 방식과 스크린샷 방식의 토큰 비용 차이를 어림해 보며 어느 방식을 쓸지 정한다(가정값 기준).
- FakePhone에 화면(쿠팡 장바구니, 블로그 글쓰기 등)을 더 넣어 내 업무 루틴을 먼저 모의로 검증한다.

## 모바일(휴대폰)에서 바로 쓰기
https://jeong-jihyun.github.io/lab/ 를 열고 '모의 스마트폰 유즈 에이전트' 카드를 눌러 값을 바꾼 뒤 **실행**을 누른다. 서버가 필요 없고, 처음 실행은 파이썬을 내려받느라 10~20초 걸린다.

## 내 컴퓨터에서 시험·실행
```
make test      # 자동 시험 (python3 -m unittest -v test_project)
make run       # 웹 화면 실행 -> http://localhost:8000 (PORT=9000 make run 으로 포트 변경)
```
- 파이썬 코드에서 직접 부르기: `from agent import api; api({...})`
- 다른 프로그램에서 부르기: `GET http://localhost:8000/api/run?키=값` (JSON 응답), 상태 확인은 `/health`

## 배포
```
make docker    # 컨테이너로 빌드·실행 (http://localhost:8000)
```
Dockerfile 이 있으므로 Render·Fly.io·Cloud Run 등 컨테이너를 받는 곳에 그대로 올릴 수 있다. 자세한 순서는 저장소의 docs/GUIDE.md 참고.
<!-- standard:end -->
