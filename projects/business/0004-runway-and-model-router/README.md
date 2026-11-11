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

<!-- standard:begin -->
## 이렇게 활용할 수 있어요
- 내 1인 기업의 하루 운영비와 런웨이(몇 일 버티는지)를 숫자를 바꿔 가며 계산한다.
- 작업 종류별로 큰 모델·작은 모델·로컬 모델 중 어디로 보낼지 규칙표를 만들고 절감률을 본다.
- 모델 가격(MODELS)과 작업 목록(TASKS)을 내 실제 값으로 고쳐 비용 시뮬레이터로 쓴다(지금 가격은 가정값).
- 프로젝트별 '이 안에 성과 없으면 중단' 기준일을 정하는 근거 자료로 쓴다.

## 모바일(휴대폰)에서 바로 쓰기
https://jeong-jihyun.github.io/lab/ 를 열고 '런웨이 계산기와 모델 라우터' 카드를 눌러 값을 바꾼 뒤 **실행**을 누른다. 서버가 필요 없고, 처음 실행은 파이썬을 내려받느라 10~20초 걸린다.

## 내 컴퓨터에서 시험·실행
```
make test      # 자동 시험 (python3 -m unittest -v test_project)
make run       # 웹 화면 실행 -> http://localhost:8000 (PORT=9000 make run 으로 포트 변경)
```
- 파이썬 코드에서 직접 부르기: `from router import api; api({...})`
- 다른 프로그램에서 부르기: `GET http://localhost:8000/api/run?키=값` (JSON 응답), 상태 확인은 `/health`

## 배포
```
make docker    # 컨테이너로 빌드·실행 (http://localhost:8000)
```
Dockerfile 이 있으므로 Render·Fly.io·Cloud Run 등 컨테이너를 받는 곳에 그대로 올릴 수 있다. 자세한 순서는 저장소의 docs/GUIDE.md 참고.
<!-- standard:end -->
