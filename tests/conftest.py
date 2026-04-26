"""Top-level fixtures shared across all test layers."""

import pytest
import sympy as sym

from ma1522 import Matrix


# ---------------------------------------------------------------------------
# Symbolic variables
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def a():
    return sym.Symbol("a", real=True)


@pytest.fixture(scope="session")
def b():
    return sym.Symbol("b", real=True)


@pytest.fixture(scope="session")
def c():
    return sym.Symbol("c", real=True)


@pytest.fixture(scope="session")
def d():
    return sym.Symbol("d", real=True)


@pytest.fixture(scope="session")
def t():
    return sym.Symbol("t", real=True)


# ---------------------------------------------------------------------------
# Numeric matrices (function-scoped so mutations don't bleed between tests)
# ---------------------------------------------------------------------------

@pytest.fixture
def mat_2x2():
    return Matrix([[1, 2], [3, 4]])


@pytest.fixture
def mat_3x3():
    return Matrix([[2, 1, 3], [0, 4, 1], [1, 2, 5]])


@pytest.fixture
def identity_2():
    return Matrix.eye(2)


@pytest.fixture
def identity_3():
    return Matrix.eye(3)


@pytest.fixture
def singular_2x2():
    return Matrix([[1, 2], [2, 4]])


@pytest.fixture
def singular_3x3():
    return Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])


# ---------------------------------------------------------------------------
# Symbolic matrices
# ---------------------------------------------------------------------------

@pytest.fixture
def sym_2x2(a, b, c, d):
    return Matrix([[a, b], [c, d]])


@pytest.fixture
def sym_col(a, b, c):
    return Matrix([[a], [b], [c]])


@pytest.fixture
def sym_row(a, b, c):
    return Matrix([[a, b, c]])


@pytest.fixture
def sym_diag(a, b):
    return Matrix.diag(a, b)
