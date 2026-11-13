# 사용법: make test(시험)  make run(실행)  make docker(컨테이너로 실행)
test:
	python3 -m unittest -v test_project

run:
	python3 server.py

install:
	pip install -r requirements.txt

docker:
	docker build -t shortform-agency-quote-planner .
	docker run --rm -p 8000:8000 shortform-agency-quote-planner
