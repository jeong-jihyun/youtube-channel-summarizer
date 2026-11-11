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
