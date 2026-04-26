"""Integration tests for linear transformations: standard_matrix."""

import pytest
import sympy as sym

from ma1522 import Matrix, PartGen


# ---------------------------------------------------------------------------
# TestStandardMatrix
# ---------------------------------------------------------------------------

class TestStandardMatrix:
    """Tests for Matrix.standard_matrix(out)."""

    def test_reconstruction_numeric(self):
        """T @ input == output for a random numeric case."""
        standard = Matrix.create_rand_matrix(3, 3)
        input_vecs = Matrix.create_rand_matrix(3, 3)
        output_vecs = standard @ input_vecs
        sol = Matrix.standard_matrix(input_vecs, output_vecs)
        assert len(sol) >= 1
        T = sol[0]
        diff = sym.simplify((T @ input_vecs - output_vecs).norm())
        assert diff == 0

    def test_known_docstring_case(self):
        """Verify the example from the docstring."""
        input_vecs = Matrix([[1, 0, 1], [2, -1, 0], [0, 3, 1]])
        output_vecs = Matrix([[4, 2, 3], [5, -1, 0], [1, 4, 2]])
        sol = Matrix.standard_matrix(input_vecs, output_vecs)
        assert len(sol) >= 1
        T = sol[0]
        expected = Matrix([
            [sym.Integer(2), sym.Integer(1), sym.Integer(1)],
            [sym.Rational(-3, 5), sym.Rational(14, 5), sym.Rational(3, 5)],
            [sym.Rational(3, 5), sym.Rational(1, 5), sym.Rational(7, 5)],
        ])
        diff = sym.simplify((T - expected).norm())
        assert diff == 0

    def test_returns_list(self):
        """standard_matrix with matrices=1 returns list[Matrix]."""
        input_vecs = Matrix([[1, 0], [0, 1]])
        output_vecs = Matrix([[2, 0], [0, 3]])
        sol = Matrix.standard_matrix(input_vecs, output_vecs)
        assert isinstance(sol, list)
        assert len(sol) >= 1
        assert isinstance(sol[0], Matrix)

    def test_identity_transformation(self):
        """T @ I == I (identity maps to itself)."""
        I = Matrix.eye(3)
        sol = Matrix.standard_matrix(I, I)
        T = sol[0]
        diff = sym.simplify((T - I).norm())
        assert diff == 0

    def test_standard_basis_columns_match(self):
        """T @ e_i == i-th column of output for each standard basis vector."""
        T_true = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        input_vecs = Matrix.eye(3)
        output_vecs = T_true @ input_vecs  # == T_true
        sol = Matrix.standard_matrix(input_vecs, output_vecs)
        T = sol[0]
        for i in range(3):
            e_i = Matrix.eye(3).select_cols(i)
            col_out = output_vecs.select_cols(i)
            result = T @ e_i
            diff = sym.simplify((result - col_out).norm())
            assert diff == 0

    def test_matrices_2_returns_partgen(self):
        """standard_matrix with matrices=2 returns list[PartGen]."""
        input_vecs = Matrix([[1, 0], [0, 1]])
        output_vecs = Matrix([[3, 1], [2, 4]])
        sol = Matrix.standard_matrix(input_vecs, output_vecs, matrices=2)
        assert isinstance(sol, list)
        assert len(sol) >= 1
        assert isinstance(sol[0], PartGen)

    def test_scaling_transformation(self):
        """Scaling by 2: output = 2 * input."""
        input_vecs = Matrix([[1, 0], [0, 1]])
        output_vecs = Matrix([[2, 0], [0, 2]])
        sol = Matrix.standard_matrix(input_vecs, output_vecs)
        T = sol[0]
        expected = 2 * Matrix.eye(2)
        diff = sym.simplify((T - expected).norm())
        assert diff == 0

    def test_reflection_transformation(self):
        """Reflection across x-axis: (x, y) -> (x, -y)."""
        input_vecs = Matrix([[1, 0], [0, 1]])
        output_vecs = Matrix([[1, 0], [0, -1]])
        sol = Matrix.standard_matrix(input_vecs, output_vecs)
        T = sol[0]
        expected = Matrix([[1, 0], [0, -1]])
        diff = sym.simplify((T - expected).norm())
        assert diff == 0
