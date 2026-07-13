.PHONY: install test lint format docs demo clean

install:
	pip install -e ".[dev,viz,docs]"

test:
	pytest -q

lint:
	ruff check .
	ruff format --check .
	mypy src/urban_tree_geometry

format:
	ruff format .
	ruff check --fix .

demo:
	python scripts/generate_sample_data.py
	python scripts/build_outputs.py
	python scripts/validate_workbook.py --reference tests/fixtures/workbook_reference.csv --report outputs/workbook_regression_report.md

docs:
	mkdocs serve

clean:
	rm -rf site build dist *.egg-info .pytest_cache .mypy_cache .ruff_cache
