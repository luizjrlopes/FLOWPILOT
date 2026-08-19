.PHONY: validate test up down
validate:
	python scripts/validate_repo.py

test:
	python -m unittest discover apps/api/tests -v

up:
	docker compose up --build

down:
	docker compose down
