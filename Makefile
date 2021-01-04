.PHONY: deps
deps:
	poetry install --remove-untracked


.PHONY: database
database: deps
	poetry run alembic upgrade head

.PHONY: format
format: isort black

.PHONY: isort
isort:
	@poetry show isort --quiet || make deps
	poetry run isort .
	@echo ''

.PHONY: black
black:
	@poetry show black --quiet || make deps
	poetry run black .
	@echo ''


.PHONY: test tests
test: tests
tests: isort_check black_check darglint mypy pylint pytest

.PHONY: isort_check
isort_check:
	@poetry show isort --quiet || make deps
	poetry run isort --check .
	@echo ''

.PHONY: black_check
black_check:
	@poetry show black --quiet || make deps
	poetry run black --check .
	@echo ''

.PHONY: darglint
darglint:
	@poetry show darglint --quiet || make deps
	find . -name '*.py' -not -path './.*' | xargs poetry run darglint -v 2
	@echo ''

.PHONY: mypy
mypy:
	@poetry show mypy --quiet || make deps
	poetry run mypy .
	@echo ''

.PHONY: pylint
pylint:
	@poetry show pylint --quiet || make deps
	find . -name '*.py' -not -path './.*' | xargs poetry run pylint --disable=fixme
	@echo ''

.PHONY: pytest
pytest:
	@poetry show pytest --quiet || make deps
	if test -z "$$CI"; then poetry run pytest; else poetry run pytest --cov --cov-report=xml; fi
	@echo ''


.PHONY: run
run: deps database
	poetry run python app.py
