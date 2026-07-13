# Contributing

Thank you for your interest in improving **urban-tree-geometry**.

## Ground rules

This project produces **preliminary geometric estimates** for outdoor lighting
pre-modelling. Contributions must preserve the clear separation between:

1. **measured / project-supplied data** (e.g. trunk perimeter);
2. **mathematically derived values** (e.g. DAP, height);
3. **adopted parameters** (H∞, k per species);
4. **engineering heuristics** (crown factors, DIALux geometry).

Never present an adopted parameter or a heuristic as if it were a field
measurement, and never claim a validation that has not been performed.

## Development setup

```bash
git clone https://github.com/czanchetta/urban-tree-geometry.git
cd urban-tree-geometry
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,viz]"
```

## Before opening a pull request

```bash
ruff check .
ruff format --check .
mypy
pytest
```

- Add or update tests for any behaviour change.
- If you change the height core, the regression test against the workbook
  fixtures must still pass (or the change must be explicitly justified).
- Keep parameters in the CSV files, not hard-coded in Python.

## Reporting issues

Please include the input data shape (anonymised), the command used, and the
full error message or warning. Do **not** attach proprietary inventory data.
