# Linear Algebra Studio

[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ma1522-linear-algebra)](https://pypi.org/project/ma1522-linear-algebra/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An interactive web application for symbolic linear algebra computations, built on the [ma1522-linear-algebra](https://github.com/YeeShin504/linear-algebra) library.

## Features

- **25 operations** — REF, RREF, LU, QR, SVD, diagonalization, eigenvalues/vectors, orthogonal complement, projection, and more
- **Symbolic engine** — exact answers using SymPy; decimal inputs are automatically converted to exact fractions
- **Chain multiplication** — multiply up to 3 matrices with optional transpose and/or inverse on each
- **Step-by-step working** — detailed breakdowns for applicable operations
- **Calculation history** — last 10 computations stored in a sidebar drawer
- **Copy results** — copy any result in parseable `[v v; v v]` format to reuse in subsequent operations
- **MathJax rendering** — LaTeX-typeset output in the browser

## Requirements

- Python 3.10 or later
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (package manager)

Install `uv` if you don't have it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Setup

### 1. Clone the repository

```bash
git clone git@github.com:Tuxedolphin/linear-algebra.git
cd linear-algebra
```

### 2. Install all dependencies

`uv sync` creates a virtual environment, installs the `ma1522` local package in editable mode, and installs all runtime and development dependencies declared in `pyproject.toml`:

```bash
uv sync
```

This installs:
- `ma1522` — the local symbolic linear algebra package (editable install)
- `numpy`, `sympy`, `sympy-latex-parser` — computation
- `fastapi`, `uvicorn`, `python-multipart` — web server
- `pytest`, `pytest-cov`, `httpx`, `ruff` — development tools

### 3. Verify the install

```bash
uv run python -c "import ma1522; print('ma1522 ok')"
```

Expected output: `ma1522 ok`

Run the test suite to confirm everything works:

```bash
uv run pytest
```

All tests should pass.

## Running the Application

Start the development server from the project root:

```bash
uv run uvicorn src.gui.app:app --port 8000 --reload
```

Then open [http://localhost:8000](http://localhost:8000) in your browser.

> **Note:** Run from the project root directory, not from inside `src/`. The server sets `PYTHONPATH` automatically via `pyproject.toml`.

## Usage

### Entering a matrix

Matrices are entered as space-separated values with rows separated by semicolons:

```
1 2 3; 4 5 6; 7 8 9
```

Decimal inputs are accepted and converted to exact fractions automatically:

```
0.5 1.5; 2.5 3.5
```

### Selecting an operation

Click any operation button (e.g. **REF**, **Eigenvalues**, **Diagonalize**) to compute. Results appear below with optional step-by-step working where available.

### Chain multiplication

Select **Chain Multiply** to multiply 2–3 matrices together. For each matrix slot, use the segment control to apply:

| Symbol | Meaning |
|--------|---------|
| `·` | No modification (use as-is) |
| `Tᵀ` | Transpose |
| `⁻¹` | Inverse |
| `(Tᵀ)⁻¹` | Transpose then inverse |

Click **+ Add Matrix** to include a third matrix, then click **Compute**.

### Copying results

After any computation, a **Copy** button appears in the result card. Clicking it copies the result in `[v v; v v]` format — paste this directly into any matrix input field to use the result in a subsequent operation.

### Calculation history

Click the clock icon button (top-right) to open the history drawer. The last 10 computations are stored per session. Click any entry to restore the inputs and result.

## Development

### Running tests

```bash
uv run pytest
```

Run only the GUI API tests:

```bash
uv run pytest tests/test_gui_api.py -v
```

### Linting

```bash
uv run ruff check src/
```

### Project structure

```
linear-algebra/
├── src/
│   ├── ma1522/          # Core symbolic linear algebra library
│   └── gui/
│       ├── app.py       # FastAPI backend — 25 operations, chain multiply
│       └── static/
│           ├── index.html
│           ├── script.js
│           └── style.css
├── tests/               # Pytest test suite
├── pyproject.toml       # Project config and dependencies
└── uv.lock              # Pinned dependency versions
```

## Credits

Original `ma1522` library and core algorithms by [YeeShin504](https://github.com/YeeShin504) and contributors.
