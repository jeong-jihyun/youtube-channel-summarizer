# 사용·시험·배포 안내

모든 모의 프로젝트는 같은 구조라서 같은 방법으로 시험하고 배포한다.

## 한눈에 보기

| 하고 싶은 일 | 방법 |
|---|---|
| 휴대폰에서 바로 써 보기 | https://jeong-jihyun.github.io/lab/ 열기 → 카드 선택 → 값 입력 → 실행 |
| 전체 시험 | `python3 scripts/check_all.py` (프로젝트 전부, 통과/실패 표) |
| 프로젝트 1개 시험 | 프로젝트 폴더에서 `make test` |
| 내 컴퓨터에서 웹으로 실행 | 프로젝트 폴더에서 `make run` → http://localhost:8000 |
| 컨테이너로 실행·배포 | 프로젝트 폴더에서 `make docker` |
| 휴대폰 실험실 갱신 | `python3 scripts/build_lab.py <블로그 저장소>/lab` 후 블로그 저장소에 커밋·push |

## 프로젝트 표준 구조

```
projects/<분류>/<번호-이름>/
├─ project.json     이름, 제목, entry(모듈:함수), script, requirements, inputs(입력칸), uses(활용 방법), video
├─ <소스>.py         핵심 코드. api(params) -> {"ok": True/False, ...} 함수를 반드시 둔다
├─ server.py        웹 화면 + JSON API (표준 라이브러리만 사용, scaffold.py 가 생성)
├─ test_project.py  자동 시험 (스크립트 실행·api 함수·웹 서버 3가지 확인)
├─ Makefile  Dockerfile  requirements.txt  .dockerignore
└─ README.md        영상 출처, 실행 결과, '표준 구역'(활용·모바일·시험·배포, 자동 생성)
```

새 프로젝트를 만들 때: 소스와 `project.json` 을 쓰고 `python3 scripts/scaffold.py projects/<분류>/<번호-이름>` 을 실행하면 나머지가 만들어진다.

## 파이썬이 어떻게 연결되어 있나

1. 핵심 코드는 `api(params)` 함수 하나로 감싼다. 입력은 문자열 딕셔너리, 출력은 `ok` 가 들어 있는 딕셔너리다.
2. **PC·서버**: `server.py` 가 같은 함수를 `GET /api/run?키=값` 으로 열어 준다. 화면(`/`)은 입력칸에서 이 주소를 부른다.
3. **휴대폰**: `build_lab.py` 가 만든 실험실 페이지가 브라우저 안의 파이썬(Pyodide)으로 같은 `api()` 를 직접 호출한다. 서버가 없다.
4. **시험**: `test_project.py` 가 스크립트 실행, `api()` 호출, 실제 웹 서버 요청을 모두 확인한다.

즉 한 개의 파이썬 함수를 코드·웹·휴대폰·시험이 같이 쓴다.

## 배포 순서

**휴대폰 실험실(정적 페이지)**: `build_lab.py` 출력 폴더를 블로그 저장소의 `lab/` 에 넣고 push 하면 https://jeong-jihyun.github.io/lab/ 에 반영된다(반영까지 1~2분).

**서버로 배포(컨테이너)**: 프로젝트 폴더의 Dockerfile 을 받는 호스팅(Render, Fly.io, Google Cloud Run 등)에서 저장소를 연결하고 폴더를 프로젝트 폴더로 지정한다. 포트는 `PORT` 환경변수를 읽는다. 비밀 키는 쓰지 않으므로 별도 설정이 없다.

## 주의

- 모든 데이터는 모의(가짜)다. 실제 계정·결제·유료 API 는 쓰지 않는다.
- 0003(코드 렌더 영상)은 numpy, pillow 가 필요하다: `pip install -r requirements.txt`. 휴대폰 실험실에서는 처음 실행 때 자동으로 내려받는다.
