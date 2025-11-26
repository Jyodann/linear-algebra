# Linear Algebra Studio

A modern, interactive Web GUI for the [ma1522-linear-algebra](https://github.com/YeeShin504/linear-algebra) library.

This project provides a user-friendly graphical interface for performing symbolic linear algebra operations, making it accessible to users without Python programming knowledge.

## Credits

**Original Library & Algorithms**: [YeeShin504](https://github.com/YeeShin504) and contributors.
This project builds upon their robust `ma1522` library to provide the underlying mathematical computations.

## Features

- **Interactive Matrix Grid**: Input matrices easily using a dynamic grid that resizes automatically.
- **Symbolic Computation**: exact results for RREF, Determinant, Inverse, Eigenvalues, and more.
- **Advanced Operations**: Support for SVD (Singular Value Decomposition) and Diagonalization.
- **Equivalent Statements**: Instantly analyze matrix properties (Rank, Invertibility, etc.) based on the MA1522 syllabus.
- **Flexible Input**: Supports Python lists, MATLAB syntax, and LaTeX.
- **Beautiful Output**: Results are rendered in standard mathematical notation using LaTeX.

## Getting Started

### Prerequisites

- Python 3.10+

### Installation

1.  Clone this repository.
2.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Running the GUI

1.  Start the local server:
    ```bash
    # From the project root directory
    export PYTHONPATH=$PYTHONPATH:$(pwd)/src && python3 -m uvicorn src.gui.app:app --reload
    ```

2.  Open your web browser and navigate to:
    [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Usage

1.  **Enter a Matrix**: Use the grid to type in numbers or symbolic expressions (e.g., `sqrt(2)`). You can also switch to text mode to paste Python lists.
2.  **Select an Operation**: Click any button in the control panel (e.g., "RREF", "Eigenvalues", "SVD").
3.  **View Results**: The result will appear below in formatted LaTeX.
4.  **Check Properties**: Click "Show Equivalent Statements" to see a categorized list of the matrix's properties.