import sys
import os
import json
import asyncio
from fastapi.testclient import TestClient

# Add src to path
sys.path.append(os.path.abspath("src"))

from gui.app import app

client = TestClient(app)

def test_rref():
    response = client.post(
        "/api/process",
        json={"matrix": "[[1, 2], [3, 4]]", "operation": "rref"}
    )
    if response.status_code != 200:
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    assert response.status_code == 200
    data = response.json()
    print("RREF Result:", data)
    assert "result" in data
    assert "1 & 0" in data["result"]

def test_eigenvals():
    response = client.post(
        "/api/process",
        json={"matrix": "[[2, 0], [0, 3]]", "operation": "eigenvals"}
    )
    assert response.status_code == 200
    data = response.json()
    print("Eigenvals Result:", data)
    assert "result" in data
    assert "2" in data["result"]
    assert "3" in data["result"]

def test_latex_input():
    response = client.post(
        "/api/process",
        json={"matrix": r"\begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix}", "operation": "det"}
    )
    assert response.status_code == 200
    data = response.json()
    print("Determinant Result:", data)
    assert "result" in data
    assert "1" in data["result"]

def test_diagonalize_with_decimals():
    response = client.post(
        "/api/process",
        json={"matrix": "[[2.0, 0.0], [0.0, 3.0]]", "operation": "diagonalize"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "error" not in data
    assert "result" in data
    assert "P" in data["result"]

def test_eigenvals_with_decimals():
    response = client.post(
        "/api/process",
        json={"matrix": "[[1.5, 0.0], [0.0, 2.5]]", "operation": "eigenvals"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "error" not in data
    assert "3/2" in data["result"] or "1.5" in data["result"] or r"\frac{3}{2}" in data["result"]

def test_raw_field_single_matrix():
    response = client.post(
        "/api/process",
        json={"matrix": "[[1, 2], [3, 4]]", "operation": "rref"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "raw" in data
    assert data["raw"].startswith("[")

def test_raw_field_decomposition():
    response = client.post(
        "/api/process",
        json={"matrix": "[[1, 2], [3, 4]]", "operation": "lu"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "raw" in data
    assert "P=" in data["raw"]
    assert "L=" in data["raw"]
    assert "U=" in data["raw"]

if __name__ == "__main__":
    try:
        test_rref()
        test_eigenvals()
        test_latex_input()
        print("All tests passed!")
    except AssertionError as e:
        print(f"Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Tests failed: {e}")
        traceback.print_exc()
        sys.exit(1)
