import json
import asyncio
from fastapi.testclient import TestClient

from gui.app import app

client = TestClient(app)


def test_rref():
    response = client.post(
        "/api/process",
        json={"matrix": "[[1, 2], [3, 4]]", "operation": "rref"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "1 & 0" in data["result"]


def test_eigenvals():
    response = client.post(
        "/api/process",
        json={"matrix": "[[2, 0], [0, 3]]", "operation": "eigenvals"}
    )
    assert response.status_code == 200
    data = response.json()
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


def test_chain_multiply_two_matrices():
    response = client.post(
        "/api/process",
        json={
            "operation": "chain_multiply",
            "matrix":  "[[1, 0], [0, 1]]",
            "matrix2": "[[2, 0], [0, 3]]",
            "mod1": "none",
            "mod2": "none",
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "error" not in data
    assert "2" in data["result"]
    assert "3" in data["result"]


def test_chain_multiply_three_matrices():
    response = client.post(
        "/api/process",
        json={
            "operation": "chain_multiply",
            "matrix":  "[[1, 0], [0, 1]]",
            "matrix2": "[[2, 0], [0, 2]]",
            "matrix3": "[[3, 0], [0, 3]]",
            "mod1": "none",
            "mod2": "none",
            "mod3": "none",
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "error" not in data
    assert "6" in data["result"]


def test_chain_multiply_transpose():
    response = client.post(
        "/api/process",
        json={
            "operation": "chain_multiply",
            "matrix":  "[[1, 2], [3, 4]]",
            "matrix2": "[[1, 2], [3, 4]]",
            "mod1": "T",
            "mod2": "none",
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "error" not in data
    assert "10" in data["result"]


def test_chain_multiply_inverse():
    response = client.post(
        "/api/process",
        json={
            "operation": "chain_multiply",
            "matrix":  "[[1, 2], [3, 4]]",
            "matrix2": "[[1, 2], [3, 4]]",
            "mod1": "inv",
            "mod2": "none",
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "error" not in data
    assert "1" in data["result"]


def test_chain_multiply_requires_two_matrices():
    response = client.post(
        "/api/process",
        json={
            "operation": "chain_multiply",
            "matrix": "[[1, 0], [0, 1]]",
            "mod1": "none",
        }
    )
    assert response.status_code == 400
    data = response.json()
    assert "error" in data


def test_chain_multiply_invalid_mod():
    response = client.post(
        "/api/process",
        json={
            "operation": "chain_multiply",
            "matrix":  "[[1, 0], [0, 1]]",
            "matrix2": "[[1, 0], [0, 1]]",
            "mod1": "badvalue",
            "mod2": "none",
        }
    )
    assert response.status_code == 400
    data = response.json()
    assert "error" in data


def test_projection_correctness():
    matrix_str = "[[1, 0], [1, 1], [1, 2]]"
    rhs_str = "[[6], [0], [0]]"
    response = client.post(
        "/api/process",
        json={"matrix": matrix_str, "rhs": rhs_str, "operation": "projection"}
    )
    assert response.status_code == 200
    data = response.json()
    result_latex = data["result"]
    assert "5" in result_latex
    assert "-3" in result_latex
    assert "2" in result_latex
    assert "-1" in result_latex
