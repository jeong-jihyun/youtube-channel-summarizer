# 0004 런웨이 계산기와 모델 라우터

## 어느 영상에서 왔나
- 제목: 2023년부터 직접 다 해본 AI 1인 기업 자동화 | THE FOUNDER EP.1
- 주소: https://www.youtube.com/watch?v=VD9OCNkJ8Dw
- 요약: [summaries/VD9OCNkJ8Dw.md](../../../summaries/VD9OCNkJ8Dw.md)

## 무엇을 하나
작업마다 필요한 품질에 맞춰 가장 싼 모델(large/small/local)을 고르고, 하루 비용과 런웨이(예산으로 버티는 날수)를 계산한다. 모든 가격은 가정값이며 실제 요금이 아니다.

## 실행 방법
```
python3 router.py
```

## 직접 실행한 결과 (2026-11-12)
```
idea_brainstorm    -> large
code_mvp           -> small
classify_comments  -> local
summarize_trends   -> local
write_ad_copy      -> small
하루 토큰비: 전부 large 7500원 / 라우팅 1900원 (절감 75%)
예산 100만원, 하루 소모 3400원 -> 런웨이 294일
성공
```

상태: **동작 확인** — 라우팅 규칙과 비용 비교 검사(assert)가 통과했다.
