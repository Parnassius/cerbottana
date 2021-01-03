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
	@poetry run which isort > /dev/null || make deps
	poetry run isort .
	@echo ''

.PHONY: black
black:
	@poetry run which black > /dev/null || make deps
	poetry run black .
	@echo ''


.PHONY: test tests
test: tests
tests: isort_check black_check darglint mypy pylint pytest

.PHONY: isort_check
isort_check:
	@poetry run which isort > /dev/null || make deps
	poetry run isort --check .
	@echo ''

.PHONY: black_check
black_check:
	@poetry run which black > /dev/null || make deps
	poetry run black --check .
	@echo ''

.PHONY: darglint
darglint:
	@poetry run which darglint > /dev/null || make deps
	find . -name '*.py' -not -path './.*' | xargs poetry run darglint -v 2
	@echo ''

.PHONY: mypy
mypy:
	@poetry run which mypy > /dev/null || make deps
	poetry run mypy .
	@echo ''

.PHONY: pylint
pylint:
	@poetry run which pylint > /dev/null || make deps
	find . -name '*.py' -not -path './.*' | xargs poetry run pylint --disable=fixme
	@echo ''

.PHONY: pytest
pytest:
	@poetry run which pytest > /dev/null || make deps
	if test -z "$$CI"; then poetry run pytest; else poetry run pytest --cov --cov-report=xml; fi
	@echo ''


.PHONY: run
run: deps database
	poetry run python app.py
