"""Unit-layer fixtures."""

import pytest
import sympy as sym

from ma1522 import Matrix
from ma1522.custom_types import ScalarFactor, PartGen


@pytest.fixture
def mat_with_aug():
    return Matrix([[1, 2, 3], [4, 5, 6]], aug_pos={2})


@pytest.fixture
def mat_gcds():
    """Matrix whose columns have obvious GCDs (6,3) and (4,8)."""
    return Matrix([[6, 4], [12, 8]])


@pytest.fixture
def sym_expr_mat():
    x = sym.Symbol("x", real=True)
    return Matrix([[x**2 - 1, x + 1], [sym.sin(x) ** 2 + sym.cos(x) ** 2, 2]])
