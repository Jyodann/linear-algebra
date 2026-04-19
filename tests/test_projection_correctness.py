import sys
import os
sys.path.append(os.path.abspath("src"))

from fastapi.testclient import TestClient
from gui.app import app
import json

client = TestClient(app)

def test_projection_correctness():
    # Example: Project b=(6, 0, 0) onto col space of A=[[1, 0], [1, 1], [1, 2]]
    # Expected Least Squares Solution x_hat = (5, -3)
    # Expected Projection p = (5, 2, -1)
    
    matrix_str = "[[1, 0, 6], [1, 1, 0], [1, 2, 0]]" # Augmented [A|b]
    
    print(f"Testing Projection with matrix: {matrix_str}")
    
    response = client.post(
        "/api/process",
        json={"matrix": matrix_str, "operation": "projection"}
    )
    
    assert response.status_code == 200
    data = response.json()
    result_latex = data["result"]
    print(f"Result: {result_latex}")
    
    # Check for x_hat = [5, -3]
    # Note: The output format is LaTeX, so we check for substrings
    # We expect something like \begin{pmatrix} 5 \\ -3 \end{pmatrix}
    assert "5" in result_latex
    assert "-3" in result_latex
    
    # Check for p = [5, 2, -1]
    assert "2" in result_latex
    assert "-1" in result_latex

if __name__ == "__main__":
    try:
        test_projection_correctness()
        print("Projection correctness test passed!")
    except AssertionError as e:
        print(f"Assertion failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
