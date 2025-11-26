# Linear Algebra Studio GUI Walkthrough

I have successfully developed a modern Web GUI for the linear algebra script. This allows users to perform symbolic matrix operations without writing any Python code.

## Features
- **Modern Interface**: A premium, dark-themed UI with responsive design.
- **Flexible Input**: Supports Python lists (e.g., `[[1, 2], [3, 4]]`), MATLAB style, and LaTeX.
- **Symbolic Operations**: Leverages the existing `ma1522` library for accurate symbolic computations.
- **Operations Supported**:
    - RREF
    - Determinant
    - Inverse
    - Eigenvalues & Eigenvectors
    - Diagonalization
    - LU & QR Decomposition

## How to Run
1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Start the Server**:
    ```bash
    uvicorn src.gui.app:app --reload
    ```
3.  **Open in Browser**:
    Navigate to [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Verification Results
Automated tests were created in `tests/test_gui_api.py` and passed successfully.
- Verified RREF calculation.
- Verified Eigenvalues calculation.
- Verified LaTeX input parsing.

## Screenshots
(Since I cannot take screenshots of the running server, here is a description of the UI)
- **Header**: "Linear Algebra Studio" with a gradient highlight.
- **Input**: Large text area for matrix input.
- **Controls**: Grid of buttons for various operations.
- **Output**: Result area rendering LaTeX output using MathJax.
