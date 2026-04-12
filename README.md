# Linear Algebra Studio

[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ma1522-linear-algebra)](https://pypi.org/project/ma1522-linear-algebra/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A modern, interactive Web GUI for the [ma1522-linear-algebra](https://github.com/YeeShin504/linear-algebra) library.

This project provides a beautiful, user-friendly graphical interface for performing symbolic linear algebra computations, making advanced operations accessible without writing any Python code.

## 🌟 Key Features

### Beautiful Web Interface
* **Interactive Matrix Editor**: Input matrices using an intuitive grid that dynamically resizes, or use text mode for LaTeX and Python lists.
* **MathJax Integration**: Outputs are beautifully typeset in LaTeX math notation, rendering complex fractions, roots, and matrices elegantly.
* **Step-by-Step Solutions**: View detailed breakdown steps for operations like REF, eigenvalues, and diagonalizations.

### Powerful Symbolic Engine
* **Core Algorithms**: Computes REF, RREF, LU Factorization, QR Factorization, SVD, and Diagonalization purely symbolically (yielding exact answers).
* **Vector Spaces**: Calculate orthogonal complements, intersections, projections, and transition matrices.
* **Equivalent Statements**: Instantly analyze matrix properties (invertibility, rank, nullity, etc.) against the MA1522 syllabus checklist.
* **Safe & Asynchronous**: Heavy operations use background threading and timeout controls to keep the UI fluid and prevent server lockups.

## 🚀 Getting Started

This project is built using modern Python tooling and highly optimized for speed.

### Prerequisites
* **Python 3.10+**
* **uv** (recommended Python package manager. [Install uv here](https://docs.astral.sh/uv/getting-started/installation/))

### Installation

1. Clone the repository:
   ```bash
   git clone git@github.com:Tuxedolphin/linear-algebra.git
   cd linear-algebra
   ```

2. Establish dependencies:
   ```bash
   # uv will automatically create a virtual environment and install dependencies
   uv sync
   ```

### Running the Application

Start the local FastAPI development server:

```bash
# Run from the root directory to ensure imports resolve
PYTHONPATH=src uv run uvicorn src.gui.app:app --port 8000 --reload
```

Finally, open your browser and navigate to: [http://localhost:8000](http://localhost:8000)

## 🤝 Credits

**Original Library & Core Algorithms**: Developed by [YeeShin504](https://github.com/YeeShin504) and contributors.
This repository extends their robust symbolic `ma1522` engine with a rich local frontend suite.
