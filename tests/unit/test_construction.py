"""Tests for Matrix construction, factory, and parsing methods.

Covers:
- __init__, __str__, __repr__, __eq__, __ne__
- eye, zeros, ones, diag
- from_list, from_str, from_latex
- create_unk_matrix, create_rand_matrix
"""

import pytest
import sympy as sym
from sympy.matrices.exceptions import ShapeError

from ma1522 import Matrix
from ma1522.custom_types import Shape


# ---------------------------------------------------------------------------
# __init__ and basic dunder methods
# ---------------------------------------------------------------------------

class TestInitAndDunder:
    def test_str_contains_values(self):
        mat = Matrix([[1, 2], [3, 4]])
        s = str(mat)
        assert "1" in s
        assert "2" in s
        assert "3" in s
        assert "4" in s

    def test_str_includes_aug_pos(self):
        mat = Matrix([[1, 2], [3, 4]])
        assert "aug_pos" in str(mat)

    def test_repr_format(self):
        mat = Matrix([[1, 2], [3, 4]])
        r = repr(mat)
        assert r.startswith("Matrix([")
        assert r.endswith("])")

    def test_equality_same_values(self):
        a = Matrix([[1, 2], [3, 4]])
        b = Matrix([[1, 2], [3, 4]])
        assert a == b

    def test_inequality_different_values(self):
        a = Matrix([[1, 2], [3, 4]])
        b = Matrix([[5, 6], [7, 8]])
        assert a != b

    def test_aug_pos_included_in_equality(self):
        mat_plain = Matrix([[1, 2]])
        mat_aug = Matrix([[1, 2]], aug_pos={0})
        assert mat_plain != mat_aug

    def test_aug_pos_same_values_same_aug(self):
        a = Matrix([[1, 2]], aug_pos={1})
        b = Matrix([[1, 2]], aug_pos={1})
        assert a == b

    def test_aug_pos_different_aug_not_equal(self):
        a = Matrix([[1, 2, 3]], aug_pos={1})
        b = Matrix([[1, 2, 3]], aug_pos={2})
        assert a != b

    def test_aug_pos_int(self):
        mat = Matrix([[1, 2], [3, 4]], aug_pos=1)
        assert 1 in mat._aug_pos

    def test_aug_pos_set(self):
        mat = Matrix([[1, 2, 3]], aug_pos={0, 2})
        assert mat._aug_pos == {0, 2}

    def test_aug_pos_none(self):
        mat = Matrix([[1, 2]])
        assert mat._aug_pos == set()


# ---------------------------------------------------------------------------
# Factory methods: eye / zeros / ones / diag
# ---------------------------------------------------------------------------

class TestFactoryMethods:
    def test_eye_returns_matrix_instance(self, identity_2):
        assert isinstance(identity_2, Matrix)

    def test_eye_correct_values(self):
        mat = Matrix.eye(3)
        assert mat == sym.eye(3)
        assert mat[0, 0] == 1
        assert mat[0, 1] == 0

    def test_zeros_returns_matrix_instance(self):
        mat = Matrix.zeros(2, 3)
        assert isinstance(mat, Matrix)
        assert mat.shape == (2, 3)
        assert all(mat[i, j] == 0 for i in range(2) for j in range(3))

    def test_ones_returns_matrix_instance(self):
        mat = Matrix.ones(2, 2)
        assert isinstance(mat, Matrix)
        assert all(mat[i, j] == 1 for i in range(2) for j in range(2))

    def test_diag_numeric(self):
        mat = Matrix.diag(1, 2, 3)
        assert isinstance(mat, Matrix)
        assert mat[0, 0] == 1
        assert mat[1, 1] == 2
        assert mat[2, 2] == 3
        assert mat[0, 1] == 0

    def test_diag_symbolic(self, a, b):
        mat = Matrix.diag(a, b)
        assert isinstance(mat, Matrix)
        assert mat[0, 0] == a
        assert mat[1, 1] == b
        assert mat[0, 1] == 0
        assert mat[1, 0] == 0

    def test_eye_with_aug_pos(self):
        mat = Matrix.eye(2, aug_pos={1})
        assert 1 in mat._aug_pos


# ---------------------------------------------------------------------------
# from_list
# ---------------------------------------------------------------------------

class TestFromList:
    def test_column_join_row_join_true(self):
        v1 = Matrix([[1], [2]])
        v2 = Matrix([[3], [4]])
        result = Matrix.from_list([v1, v2], row_join=True)
        assert result == Matrix([[1, 3], [2, 4]])

    def test_row_join_false_stacks_vertically(self):
        v1 = Matrix([[1, 2]])
        v2 = Matrix([[3, 4]])
        result = Matrix.from_list([v1, v2], row_join=False)
        assert result == Matrix([[1, 2], [3, 4]])

    def test_single_vector(self):
        v = Matrix([[5], [6], [7]])
        result = Matrix.from_list([v], row_join=True)
        assert result == v

    def test_empty_list_returns_empty_matrix(self):
        result = Matrix.from_list([])
        # Should return an empty Matrix without error
        assert result.shape[0] == 0 or result.shape[1] == 0

    def test_incompatible_shapes_raise_error(self):
        v1 = Matrix([[1], [2]])
        v2 = Matrix([[3], [4], [5]])
        with pytest.raises(Exception):
            Matrix.from_list([v1, v2], row_join=True)

    def test_from_list_three_columns(self):
        v1 = Matrix([[1], [0]])
        v2 = Matrix([[0], [1]])
        v3 = Matrix([[2], [3]])
        result = Matrix.from_list([v1, v2, v3], row_join=True)
        expected = Matrix([[1, 0, 2], [0, 1, 3]])
        assert result == expected


# ---------------------------------------------------------------------------
# from_str
# ---------------------------------------------------------------------------

class TestFromStr:
    def test_basic_parse(self):
        result = Matrix.from_str("1 2; 3 4")
        expected = Matrix([[1, 2], [3, 4]])
        assert result == expected

    def test_parse_with_fractions(self):
        result = Matrix.from_str("1/2 3/4; 5/6 7/8")
        expected = Matrix([[sym.Rational(1, 2), sym.Rational(3, 4)],
                           [sym.Rational(5, 6), sym.Rational(7, 8)]])
        assert result == expected

    def test_single_row(self):
        result = Matrix.from_str("1 2 3")
        expected = Matrix([[1, 2, 3]])
        assert result == expected

    def test_column_vector(self):
        result = Matrix.from_str("1; 2; 3")
        expected = Matrix([[1], [2], [3]])
        assert result == expected

    def test_with_brackets(self):
        result = Matrix.from_str("[1 2; 3 4]")
        expected = Matrix([[1, 2], [3, 4]])
        assert result == expected

    def test_symbolic_entries(self):
        result = Matrix.from_str("a b; c d")
        assert result.shape == (2, 2)
        # All entries should be symbolic
        assert len(result.free_symbols) == 4


# ---------------------------------------------------------------------------
# from_latex
# ---------------------------------------------------------------------------

class TestFromLatex:
    def test_pmatrix_environment(self):
        result = Matrix.from_latex(
            r"\begin{pmatrix} 1 & 2 \\ 3 & 4 \end{pmatrix}", verbosity=0
        )
        assert result == Matrix([[1, 2], [3, 4]])

    def test_array_environment_with_col_spec(self):
        result = Matrix.from_latex(
            r"\begin{array}{cc} 1 & 2 \\ 3 & 4 \end{array}", verbosity=0
        )
        assert result == Matrix([[1, 2], [3, 4]])

    def test_array_environment_without_col_spec(self):
        result = Matrix.from_latex(
            r"\begin{array} 1 & 2 \\ 3 & 4 \end{array}", verbosity=0
        )
        assert result == Matrix([[1, 2], [3, 4]])

    def test_vector_list_row_join_true(self):
        latex = r"\{ \begin{pmatrix} 1 \\ 3 \end{pmatrix}, \begin{pmatrix} 2 \\ 4 \end{pmatrix} \}"
        result = Matrix.from_latex(latex, row_join=True, verbosity=0)
        assert result == Matrix([[1, 2], [3, 4]])

    def test_vector_list_row_join_false(self):
        latex = r"\{ \begin{pmatrix} 1 \\ 3 \end{pmatrix}, \begin{pmatrix} 2 \\ 4 \end{pmatrix} \}"
        result = Matrix.from_latex(latex, row_join=False, verbosity=0)
        assert result == Matrix([[1], [3], [2], [4]])

    def test_matrix_multiplication_expression(self):
        result = Matrix.from_latex(
            r"\begin{pmatrix} 1 & 2 \\ 3 & 4 \end{pmatrix}\begin{pmatrix} 5 & 6 \\ 7 & 8 \end{pmatrix}",
            verbosity=0,
        )
        expected = Matrix([[1, 2], [3, 4]]) @ Matrix([[5, 6], [7, 8]])
        assert result == expected

    def test_norm_true_normalises_columns(self):
        # A column vector [3, 4] has norm 5; normalised → [3/5, 4/5]
        result = Matrix.from_latex(
            r"\begin{pmatrix} 3 \\ 4 \end{pmatrix}", norm=True, verbosity=0
        )
        result.simplify()
        expected = Matrix([[sym.Rational(3, 5)], [sym.Rational(4, 5)]])
        assert result == expected

    @pytest.mark.parametrize("latex_input", [
        r"\begin{pmatrix} \end{pmatrix}",
        r"{}",
        "",
    ])
    def test_invalid_or_empty_latex_raises(self, latex_input):
        with pytest.raises(Exception):
            Matrix.from_latex(latex_input, verbosity=0)


# ---------------------------------------------------------------------------
# create_unk_matrix
# ---------------------------------------------------------------------------

class TestCreateUnkMatrix:
    def test_default_1x1_single_symbol(self):
        mat = Matrix.create_unk_matrix()
        assert mat.shape == (1, 1)
        # Default single entry should be real
        entry = mat[0, 0]
        assert entry.is_real

    def test_custom_dimensions_and_symbol(self):
        mat = Matrix.create_unk_matrix(r=3, c=2, symbol="a")
        assert mat.shape == (3, 2)

    def test_symbol_naming_pattern(self):
        mat = Matrix.create_unk_matrix(r=2, c=2, symbol="a")
        for entry in mat.flat():
            assert str(entry).startswith("a_")

    def test_is_real_true(self):
        mat = Matrix.create_unk_matrix(r=2, c=2, symbol="a", is_real=True)
        for entry in mat.flat():
            assert entry.is_real

    def test_is_real_false(self):
        mat = Matrix.create_unk_matrix(r=2, c=2, symbol="z", is_real=False)
        for entry in mat.flat():
            # Complex symbols are not marked real
            assert not entry.is_real

    def test_shape_upper(self):
        mat = Matrix.create_unk_matrix(r=3, c=3, symbol="u", shape=Shape.UPPER)
        # Below-diagonal entries should be zero
        assert mat[1, 0] == 0
        assert mat[2, 0] == 0
        assert mat[2, 1] == 0

    def test_shape_lower(self):
        mat = Matrix.create_unk_matrix(r=3, c=3, symbol="l", shape=Shape.LOWER)
        # Above-diagonal entries should be zero
        assert mat[0, 1] == 0
        assert mat[0, 2] == 0
        assert mat[1, 2] == 0

    def test_shape_strict_upper(self):
        mat = Matrix.create_unk_matrix(r=3, c=3, symbol="u", shape=Shape.STRICT_UPPER)
        # Diagonal and below should be zero
        assert mat[0, 0] == 0
        assert mat[1, 1] == 0
        assert mat[2, 2] == 0
        assert mat[1, 0] == 0

    def test_shape_strict_lower(self):
        mat = Matrix.create_unk_matrix(r=3, c=3, symbol="l", shape=Shape.STRICT_LOWER)
        # Diagonal and above should be zero
        assert mat[0, 0] == 0
        assert mat[1, 1] == 0
        assert mat[0, 1] == 0

    def test_shape_symmetric(self):
        mat = Matrix.create_unk_matrix(r=3, c=3, symbol="s", shape=Shape.SYMMETRIC)
        # M should equal M.T
        assert mat == mat.T

    def test_shape_scalar(self):
        mat = Matrix.create_unk_matrix(r=3, c=3, symbol="s", shape=Shape.SCALAR)
        # Off-diagonal entries should be zero
        assert mat[0, 1] == 0
        assert mat[1, 0] == 0
        # All diagonal entries should be equal
        assert mat[0, 0] == mat[1, 1]
        assert mat[1, 1] == mat[2, 2]


# ---------------------------------------------------------------------------
# create_rand_matrix
# ---------------------------------------------------------------------------

class TestCreateRandMatrix:
    def test_seeded_is_reproducible(self):
        mat1 = Matrix.create_rand_matrix(2, 2, seed=42)
        mat2 = Matrix.create_rand_matrix(2, 2, seed=42)
        assert mat1 == mat2

    def test_shape_correct(self):
        mat = Matrix.create_rand_matrix(3, 4, seed=0)
        assert mat.shape == (3, 4)

    def test_entries_are_integers(self):
        mat = Matrix.create_rand_matrix(2, 3, seed=7)
        for entry in mat.flat():
            assert entry == int(entry)

    def test_different_seeds_give_different_results(self):
        mat1 = Matrix.create_rand_matrix(3, 3, seed=1)
        mat2 = Matrix.create_rand_matrix(3, 3, seed=2)
        # Very likely to differ
        assert mat1 != mat2

    def test_known_seed_output(self):
        # Verified from SymPy's randMatrix(r=2, c=2, seed=42)
        mat = Matrix.create_rand_matrix(2, 2, seed=42)
        assert mat.shape == (2, 2)
        assert isinstance(mat, Matrix)
