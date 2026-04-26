"""Tests for Matrix arithmetic operators and algebraic operations.

Covers:
- Addition / Subtraction
- Scalar multiplication
- Matrix multiplication (@)
- Negation (__neg__)
- Transpose (.T property)
- Power (**) operator
- Absolute value (__abs__)
"""

import pytest
import sympy as sym
from sympy.matrices.exceptions import ShapeError

from ma1522 import Matrix


# ---------------------------------------------------------------------------
# Addition / Subtraction
# ---------------------------------------------------------------------------

class TestAdditionSubtraction:
    def test_numeric_addition_element_wise(self):
        a = Matrix([[1, 2], [3, 4]])
        b = Matrix([[5, 6], [7, 8]])
        assert a + b == Matrix([[6, 8], [10, 12]])

    def test_numeric_subtraction_element_wise(self):
        a = Matrix([[5, 6], [7, 8]])
        b = Matrix([[1, 2], [3, 4]])
        assert a - b == Matrix([[4, 4], [4, 4]])

    def test_symbolic_addition(self, sym_2x2, a, b, c, d):
        result = sym_2x2 + sym_2x2
        expected = 2 * sym_2x2
        diff = sym.simplify(result - expected)
        assert diff == Matrix.zeros(2, 2)

    def test_aug_pos_union_on_add(self):
        a = Matrix([[1, 2], [3, 4]], aug_pos={1})
        b = Matrix([[5, 6], [7, 8]], aug_pos={0})
        result = a + b
        assert result._aug_pos == {0, 1}

    def test_aug_pos_union_on_sub(self):
        a = Matrix([[1, 2], [3, 4]], aug_pos={1})
        b = Matrix([[5, 6], [7, 8]], aug_pos={0})
        result = a - b
        assert result._aug_pos == {0, 1}

    def test_incompatible_shapes_addition_raises(self):
        a = Matrix([[1, 2]])
        b = Matrix([[1, 2], [3, 4]])
        with pytest.raises((ShapeError, ValueError)):
            _ = a + b

    def test_incompatible_shapes_subtraction_raises(self):
        a = Matrix([[1, 2]])
        b = Matrix([[1, 2], [3, 4]])
        with pytest.raises((ShapeError, ValueError)):
            _ = a - b

    def test_zero_matrix_is_additive_identity(self, mat_2x2):
        zero = Matrix.zeros(2, 2)
        # mat_2x2 + zero should equal mat_2x2 element-wise
        result = mat_2x2 + zero
        assert result[0, 0] == mat_2x2[0, 0]
        assert result[1, 1] == mat_2x2[1, 1]


# ---------------------------------------------------------------------------
# Scalar multiplication
# ---------------------------------------------------------------------------

class TestScalarMultiplication:
    def test_left_scalar_multiplication(self, mat_2x2):
        result = 2 * mat_2x2
        assert result == Matrix([[2, 4], [6, 8]])

    def test_right_scalar_multiplication(self, mat_2x2):
        result = mat_2x2 * 2
        assert result == Matrix([[2, 4], [6, 8]])

    def test_left_and_right_commute(self, mat_2x2):
        assert 2 * mat_2x2 == mat_2x2 * 2

    def test_symbolic_scalar_multiplication(self, mat_2x2, a):
        result = a * mat_2x2
        assert result == Matrix([[a, 2 * a], [3 * a, 4 * a]])

    def test_rational_scalar_multiplication(self, mat_2x2):
        result = mat_2x2 * sym.Rational(1, 2)
        assert result == Matrix([[sym.Rational(1, 2), 1],
                                 [sym.Rational(3, 2), 2]])

    def test_aug_pos_preserved_on_scalar_mul(self):
        mat = Matrix([[1, 2]], aug_pos={0})
        result = 3 * mat
        assert result._aug_pos == {0}

    def test_zero_scalar_gives_zero_matrix(self, mat_2x2):
        result = 0 * mat_2x2
        assert result == Matrix.zeros(2, 2)


# ---------------------------------------------------------------------------
# Matrix multiplication (@)
# ---------------------------------------------------------------------------

class TestMatrixMultiplication:
    def test_identity_is_right_identity(self, mat_2x2, identity_2):
        assert mat_2x2 @ identity_2 == mat_2x2

    def test_identity_is_left_identity(self, mat_2x2, identity_2):
        assert identity_2 @ mat_2x2 == mat_2x2

    def test_concrete_product(self):
        A = Matrix([[1, 2], [3, 4]])
        B = Matrix([[5, 6], [7, 8]])
        expected = Matrix([[19, 22], [43, 50]])
        assert A @ B == expected

    def test_symbolic_matmul_with_identity(self, sym_2x2, identity_2):
        result = sym_2x2 @ identity_2
        diff = sym.simplify(result - sym_2x2)
        assert diff == Matrix.zeros(2, 2)

    def test_shape_mismatch_raises(self):
        A = Matrix([[1, 2, 3]])  # 1x3
        B = Matrix([[1, 2], [3, 4]])  # 2x2
        with pytest.raises((ShapeError, ValueError)):
            _ = A @ B

    def test_non_square_multiplication(self):
        A = Matrix([[1, 2, 3], [4, 5, 6]])  # 2x3
        B = Matrix([[7], [8], [9]])  # 3x1
        result = A @ B
        assert result.shape == (2, 1)
        assert result[0, 0] == 1*7 + 2*8 + 3*9
        assert result[1, 0] == 4*7 + 5*8 + 6*9

    def test_3x3_concrete_product(self, mat_3x3, identity_3):
        assert mat_3x3 @ identity_3 == mat_3x3

    @pytest.mark.parametrize("n", [1, 2, 3])
    def test_identity_n_matmul(self, n):
        I = Matrix.eye(n)
        A = Matrix.create_rand_matrix(n, n, seed=n)
        assert A @ I == A
        assert I @ A == A


# ---------------------------------------------------------------------------
# Negation (__neg__)
# ---------------------------------------------------------------------------

class TestNegation:
    def test_negation_negates_all_entries(self, mat_2x2):
        result = -mat_2x2
        assert result == Matrix([[-1, -2], [-3, -4]])

    def test_double_negation_is_identity(self, mat_2x2):
        assert -(-mat_2x2) == mat_2x2

    def test_aug_pos_preserved_under_negation(self):
        mat = Matrix([[1, 2], [3, 4]], aug_pos={1})
        negated = -mat
        assert negated._aug_pos == {1}

    def test_negation_symbolic(self, sym_2x2, a, b, c, d):
        result = -sym_2x2
        assert result == Matrix([[-a, -b], [-c, -d]])

    def test_negation_plus_original_is_zero(self, mat_3x3):
        result = mat_3x3 + (-mat_3x3)
        assert result == Matrix.zeros(3, 3)


# ---------------------------------------------------------------------------
# Transpose (.T property)
# ---------------------------------------------------------------------------

class TestTranspose:
    def test_basic_transpose(self):
        mat = Matrix([[1, 2], [3, 4]])
        assert mat.T == Matrix([[1, 3], [2, 4]])

    def test_double_transpose_is_identity(self, mat_2x2):
        assert (mat_2x2.T).T == mat_2x2

    def test_symbolic_transpose(self, a, b, c, d):
        mat = Matrix([[a, b], [c, d]])
        assert mat.T == Matrix([[a, c], [b, d]])

    def test_transpose_returns_matrix_instance(self, mat_2x2):
        assert isinstance(mat_2x2.T, Matrix)

    def test_transpose_non_square(self):
        mat = Matrix([[1, 2, 3], [4, 5, 6]])  # 2x3
        t = mat.T  # 3x2
        assert t.shape == (3, 2)
        assert t[0, 0] == 1
        assert t[2, 1] == 6

    def test_at_commutes_with_transpose(self, mat_2x2):
        # (A @ B).T == B.T @ A.T
        A = mat_2x2
        B = Matrix([[1, 0], [0, 2]])
        assert (A @ B).T == B.T @ A.T


# ---------------------------------------------------------------------------
# Power (**) operator
# ---------------------------------------------------------------------------

class TestPower:
    def test_power_zero_is_identity(self, mat_2x2, identity_2):
        result = mat_2x2 ** 0
        assert result == identity_2

    def test_power_one_is_self(self, mat_2x2):
        result = mat_2x2 ** 1
        assert result == mat_2x2

    def test_power_two_is_matmul(self, mat_2x2):
        result = mat_2x2 ** 2
        expected = mat_2x2 @ mat_2x2
        assert result == expected

    def test_power_three(self, mat_2x2):
        result = mat_2x2 ** 3
        expected = mat_2x2 @ mat_2x2 @ mat_2x2
        assert result == expected

    def test_identity_power(self, identity_2):
        for n in range(5):
            assert identity_2 ** n == identity_2


# ---------------------------------------------------------------------------
# Absolute value (__abs__)
# ---------------------------------------------------------------------------

class TestAbsoluteValue:
    def test_abs_returns_matrix(self):
        mat = Matrix([[1, -2], [-3, 4]])
        result = abs(mat)
        assert isinstance(result, Matrix)

    def test_abs_values(self):
        mat = Matrix([[1, -2], [-3, 4]])
        result = abs(mat)
        assert result[0, 0] == 1
        assert result[0, 1] == 2
        assert result[1, 0] == 3
        assert result[1, 1] == 4

    def test_abs_preserves_aug_pos(self):
        mat = Matrix([[1, -2], [-3, 4]], aug_pos={1})
        result = abs(mat)
        assert result._aug_pos == {1}

    def test_abs_of_positive_entries_unchanged(self):
        mat = Matrix([[1, 2], [3, 4]])
        result = abs(mat)
        assert result == mat
