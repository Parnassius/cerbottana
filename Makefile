.PHONY: all
all: tests


poetry.lock: pyproject.toml
	@poetry lock --no-update

.venv/.flag: poetry.lock
	@poetry config --local virtualenvs.in-project true
	@poetry install --remove-untracked
	@touch .venv/.flag

.PHONY: deps
deps: .venv/.flag


.PHONY: database
database: deps
	poetry run alembic upgrade head


.PHONY: format
format: isort black

.PHONY: isort
isort: deps
	poetry run isort .
	@echo ''

.PHONY: black
black: deps
	poetry run black .
	@echo ''


.PHONY: test tests
test: tests
tests: isort_check black_check darglint mypy pylint pytest

.PHONY: isort_check
isort_check: deps
	poetry run isort --check .
	@echo ''

.PHONY: black_check
black_check: deps
	poetry run black --check .
	@echo ''

.PHONY: darglint
darglint: deps
	find . -name '*.py' -not -path './.*' | xargs poetry run darglint -v 2
	@echo ''

.PHONY: mypy
mypy: deps
	poetry run mypy .
	@echo ''

.PHONY: pylint
pylint: deps
	find . -name '*.py' -not -path './.*' | xargs poetry run pylint --disable=fixme
	@echo ''

.PHONY: pytest
pytest: deps
	if test -z "$$CI"; then poetry run pytest; else poetry run pytest --cov --cov-report=xml; fi
	@echo ''


.PHONY: run
run: deps database
	poetry run python app.py
