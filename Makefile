.PHONY: install test lint format clean run

install:
	pip install -e ".[dev]"

test:
	pytest -v --cov=. --cov-report=term-missing

lint:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics
	mypy .

format:
	black .

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache htmlcov/
	rm -f .coverage coverage.xml translated_news.xml .translation_cache.json

run:
	python main.py
