"""Integration-layer fixtures."""

import pytest
import sympy as sym

from ma1522 import Matrix


@pytest.fixture
def overdetermined():
    """Overdetermined system: 3 equations, 2 unknowns (no exact solution)."""
    A = Matrix([[0, 1], [1, 1], [2, 1]])
    b = Matrix([[6], [0], [0]])
    return A, b


@pytest.fixture
def underdetermined():
    """Underdetermined system: more unknowns than equations."""
    return Matrix([[1, 1, 1], [0, 1, 2]])


@pytest.fixture
def stochastic_2x2():
    return Matrix([[sym.Rational(4, 5), sym.Rational(3, 10)],
                   [sym.Rational(1, 5), sym.Rational(7, 10)]])


@pytest.fixture
def sym_invertible(a, b):
    """Symbolic 2×2 with non-zero determinant (a²-b² assumed non-zero)."""
    return Matrix([[a, b], [b, a]])


@pytest.fixture
def orthog_cols():
    """Matrix with two already-orthogonal columns."""
    return Matrix([[1, 0], [0, 1], [0, 0]])
