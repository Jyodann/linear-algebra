"""Tests for Matrix manipulation methods.

Covers:
- copy, subs, simplify, identify
- select_cols, select_rows, sep_part_gen
- scalar_factor, aug_line, rm_aug_line
- row_join, col_join
- scale_row, swap_row, reduce_row
- get_pivot_row, get_pivot_pos, get_pivot_elements
"""

import pytest
import sympy as sym
from sympy.matrices.exceptions import ShapeError

from ma1522 import Matrix, PartGen, ScalarFactor


# ---------------------------------------------------------------------------
# copy
# ---------------------------------------------------------------------------

class TestCopy:
    def test_value_equality(self, mat_2x2):
        copied = mat_2x2.copy()
        assert copied == mat_2x2

    def test_identity_inequality(self, mat_2x2):
        copied = mat_2x2.copy()
        assert copied is not mat_2x2

    def test_aug_pos_preserved(self, mat_with_aug):
        copied = mat_with_aug.copy()
        assert copied._aug_pos == mat_with_aug._aug_pos

    def test_mutating_copy_does_not_affect_original(self, mat_2x2):
        copied = mat_2x2.copy()
        copied[0, 0] = 999
        assert mat_2x2[0, 0] == 1  # original unchanged


# ---------------------------------------------------------------------------
# subs
# ---------------------------------------------------------------------------

class TestSubs:
    def test_numeric_substitution(self, a, b, c, d):
        mat = Matrix([[a, b], [c, d]])
        result = mat.subs([(a, 1), (b, 2), (c, 3), (d, 4)])
        expected = Matrix([[1, 2], [3, 4]])
        assert result == expected

    def test_chained_substitution(self, a, b):
        mat = Matrix([[a + b]])
        step1 = mat.subs(a, 1)
        step2 = step1.subs(b, 2)
        assert step2 == Matrix([[3]])

    def test_aug_pos_preserved_through_subs(self, a, b):
        mat = Matrix([[a, b]], aug_pos={0})
        result = mat.subs([(a, 1), (b, 2)])
        assert result._aug_pos == {0}

    def test_partial_substitution(self, a, b):
        mat = Matrix([[a, b], [a + b, a - b]])
        result = mat.subs(a, 0)
        assert result == Matrix([[0, b], [b, -b]])


# ---------------------------------------------------------------------------
# simplify
# ---------------------------------------------------------------------------

class TestSimplify:
    def test_trig_identity_simplifies(self, sym_expr_mat):
        """sin^2(x) + cos^2(x) should simplify to 1."""
        mat = sym_expr_mat.copy()
        mat.simplify()
        # Position [1,0] was sin(x)**2 + cos(x)**2
        assert mat[1, 0] == 1

    def test_simplify_modifies_in_place(self):
        x = sym.Symbol("x", real=True)
        mat = Matrix([[sym.sin(x) ** 2 + sym.cos(x) ** 2]])
        mat.simplify()
        assert mat[0, 0] == 1

    def test_simplify_returns_none(self):
        mat = Matrix([[1, 2], [3, 4]])
        result = mat.simplify()
        assert result is None

    def test_rational_matrix_unchanged(self):
        mat = Matrix([[sym.Rational(1, 2), sym.Rational(3, 4)]])
        original = mat.copy()
        mat.simplify()
        assert mat == original


# ---------------------------------------------------------------------------
# identify
# ---------------------------------------------------------------------------

class TestIdentify:
    def test_float_close_to_integer(self):
        # 1.0000000000001 identified as 1 but residue is non-zero → RuntimeWarning
        mat = Matrix([[1.0000000000001, 2.0], [3.0, 4.0]])
        with pytest.warns(RuntimeWarning):
            identified = mat.identify(tol=1e-10)
        diff = (identified - Matrix([[1, 2], [3, 4]])).norm()
        assert diff < 1e-9

    def test_no_warning_exact_floats(self):
        # Exact integer floats → no residue → no warning
        mat = Matrix([[2.0, 3.0]])
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            mat.identify()  # should not raise


# ---------------------------------------------------------------------------
# select_cols
# ---------------------------------------------------------------------------

class TestSelectCols:
    def test_single_column(self):
        mat = Matrix([[1, 2, 3], [4, 5, 6]])
        result = mat.select_cols(1)
        assert result == Matrix([[2], [5]])

    def test_multiple_columns_in_order(self):
        mat = Matrix([[1, 2, 3], [4, 5, 6]])
        result = mat.select_cols(0, 2)
        assert result == Matrix([[1, 3], [4, 6]])

    def test_negative_index(self):
        mat = Matrix([[1, 2, 3], [4, 5, 6]])
        result = mat.select_cols(-1)
        assert result == Matrix([[3], [6]])

    def test_out_of_range_raises(self):
        mat = Matrix([[1, 2], [3, 4]])
        with pytest.raises(IndexError):
            mat.select_cols(5)


# ---------------------------------------------------------------------------
# select_rows
# ---------------------------------------------------------------------------

class TestSelectRows:
    def test_single_row(self):
        mat = Matrix([[1, 2, 3], [4, 5, 6]])
        result = mat.select_rows(0)
        assert result == Matrix([[1, 2, 3]])

    def test_multiple_rows(self):
        mat = Matrix([[1, 2], [3, 4], [5, 6]])
        result = mat.select_rows(0, 2)
        assert result == Matrix([[1, 2], [5, 6]])

    def test_out_of_range_raises(self):
        mat = Matrix([[1, 2], [3, 4]])
        with pytest.raises(IndexError):
            mat.select_rows(5)


# ---------------------------------------------------------------------------
# sep_part_gen
# ---------------------------------------------------------------------------

class TestSepPartGen:
    def test_basic_separation(self, a, b):
        mat = Matrix([[a + 1, b], [2, a + b]])
        pg = mat.sep_part_gen()
        assert isinstance(pg, PartGen)
        assert pg.part_sol == Matrix([[1, 0], [2, 0]])
        assert pg.gen_sol == Matrix([[a, b], [0, a + b]])

    def test_no_free_symbols(self):
        mat = Matrix([[1, 2], [3, 4]])
        pg = mat.sep_part_gen()
        assert pg.part_sol == mat
        assert pg.gen_sol == Matrix.zeros(2, 2)

    def test_eval_reconstructs_original(self, a, b):
        mat = Matrix([[a + 1, b], [2, a + b]])
        pg = mat.sep_part_gen()
        reconstructed = pg.eval()
        diff = sym.simplify(reconstructed - mat)
        assert diff == Matrix.zeros(2, 2)


# ---------------------------------------------------------------------------
# scalar_factor
# ---------------------------------------------------------------------------

class TestScalarFactor:
    def test_column_factorisation(self):
        mat = Matrix([[6, 4], [12, 8]])
        sf = mat.scalar_factor(column=True)
        assert isinstance(sf, ScalarFactor)
        assert sf.full == Matrix([[1, 1], [2, 2]])
        assert sf.diag == Matrix.diag(6, 4)
        assert sf.order == "FD"

    def test_column_factorisation_reconstructs(self):
        mat = Matrix([[6, 4], [12, 8]])
        sf = mat.scalar_factor(column=True)
        assert sf.eval() == mat

    def test_row_factorisation(self):
        mat = Matrix([[6, 12], [4, 8]])
        sf = mat.scalar_factor(column=False)
        assert isinstance(sf, ScalarFactor)
        assert sf.order == "DF"
        assert sf.eval() == mat

    def test_symbolic_does_not_raise(self, a):
        """Symbolic matrix should not trigger assertion error."""
        mat = Matrix([[a, 2 * a], [3 * a, 4 * a]])
        sf = mat.scalar_factor(column=True)
        assert isinstance(sf, ScalarFactor)


# ---------------------------------------------------------------------------
# aug_line / rm_aug_line
# ---------------------------------------------------------------------------

class TestAugLine:
    def test_default_pos_adds_last_column(self):
        mat = Matrix([[1, 2], [3, 4]])
        mat.aug_line()  # default -1 → ncols-1 = 1
        assert 1 in mat._aug_pos

    def test_specific_pos(self):
        mat = Matrix([[1, 2, 3], [4, 5, 6]])
        mat.aug_line(1)
        assert 1 in mat._aug_pos

    def test_multiple_aug_lines_accumulate(self):
        mat = Matrix([[1, 2, 3, 4]])
        mat.aug_line(0)
        mat.aug_line(2)
        assert {0, 2}.issubset(mat._aug_pos)

    def test_invalid_pos_raises(self):
        mat = Matrix([[1, 2], [3, 4]])
        with pytest.raises(IndexError):
            mat.aug_line(10)

    def test_rm_aug_line_specific_pos(self):
        mat = Matrix([[1, 2, 3]], aug_pos={1})
        mat.rm_aug_line(1)
        assert 1 not in mat._aug_pos

    def test_rm_aug_line_none_clears_all(self):
        mat = Matrix([[1, 2, 3]], aug_pos={0, 2})
        mat.rm_aug_line(None)
        assert mat._aug_pos == set()

    def test_rm_aug_line_nonexistent_pos_is_noop(self):
        mat = Matrix([[1, 2]], aug_pos={0})
        mat.rm_aug_line(1)  # 1 was not in aug_pos
        assert 0 in mat._aug_pos  # original unchanged


# ---------------------------------------------------------------------------
# row_join / col_join
# ---------------------------------------------------------------------------

class TestRowJoinColJoin:
    def test_row_join_dimensions(self):
        a = Matrix([[1, 2], [3, 4]])
        b = Matrix([[5], [6]])
        result = a.row_join(b)
        assert result.shape == (2, 3)

    def test_row_join_values(self):
        a = Matrix([[1, 2], [3, 4]])
        b = Matrix([[5], [6]])
        result = a.row_join(b, aug_line=False)
        assert result == Matrix([[1, 2, 5], [3, 4, 6]])

    def test_row_join_with_aug_line_adds_boundary(self):
        a = Matrix([[1, 2]])
        b = Matrix([[3]])
        result = a.row_join(b, aug_line=True)
        # Boundary at column index self.cols - 1 = 1
        assert 1 in result._aug_pos

    def test_row_join_without_aug_line(self):
        a = Matrix([[1, 2]])
        b = Matrix([[3]])
        result = a.row_join(b, aug_line=False)
        assert 1 not in result._aug_pos

    def test_row_join_propagates_other_aug_pos(self):
        a = Matrix([[1, 2]])
        b = Matrix([[3, 4]], aug_pos={0})
        result = a.row_join(b, aug_line=False)
        # b's aug_pos 0 shifted by len(a.cols)=2 → 2
        assert 2 in result._aug_pos

    def test_col_join_dimensions(self):
        a = Matrix([[1, 2]])
        b = Matrix([[3, 4]])
        result = a.col_join(b)
        assert result.shape == (2, 2)

    def test_col_join_values(self):
        a = Matrix([[1, 2]])
        b = Matrix([[3, 4]])
        result = a.col_join(b)
        assert result == Matrix([[1, 2], [3, 4]])

    def test_col_join_intersects_aug_pos(self):
        a = Matrix([[1, 2]], aug_pos={0})
        b = Matrix([[3, 4]], aug_pos={0})
        result = a.col_join(b)
        assert 0 in result._aug_pos

    def test_col_join_non_shared_aug_pos_dropped(self):
        a = Matrix([[1, 2]], aug_pos={0})
        b = Matrix([[3, 4]], aug_pos={1})
        result = a.col_join(b)
        # Intersection is empty
        assert result._aug_pos == set()

    def test_row_join_incompatible_rows_raises(self):
        a = Matrix([[1, 2]])
        b = Matrix([[3], [4]])
        with pytest.raises(ShapeError):
            a.row_join(b)

    def test_col_join_incompatible_cols_raises(self):
        a = Matrix([[1, 2]])
        b = Matrix([[3, 4, 5]])
        with pytest.raises(ShapeError):
            a.col_join(b)


# ---------------------------------------------------------------------------
# scale_row
# ---------------------------------------------------------------------------

class TestScaleRow:
    def test_numeric_scalar(self):
        mat = Matrix([[1, 2], [3, 4]])
        result = mat.scale_row(0, 2, verbosity=0)
        assert result[0, 0] == 2
        assert result[0, 1] == 4
        assert result[1, 0] == 3  # unchanged

    def test_symbolic_scalar(self, a):
        mat = Matrix([[1, 2], [3, 4]])
        mat.scale_row(0, a, verbosity=0)
        assert mat[0, 0] == a
        assert mat[0, 1] == 2 * a

    def test_modifies_in_place(self):
        mat = Matrix([[5, 6], [7, 8]])
        mat.scale_row(1, 3, verbosity=0)
        assert mat[1, 0] == 21
        assert mat[1, 1] == 24


# ---------------------------------------------------------------------------
# swap_row
# ---------------------------------------------------------------------------

class TestSwapRow:
    def test_basic_swap(self):
        mat = Matrix([[1, 2], [3, 4]])
        mat.swap_row(0, 1, verbosity=0)
        assert mat[0, 0] == 3
        assert mat[0, 1] == 4
        assert mat[1, 0] == 1
        assert mat[1, 1] == 2

    def test_swap_same_row_is_noop(self):
        mat = Matrix([[1, 2], [3, 4]])
        original = mat.copy()
        mat.swap_row(0, 0, verbosity=0)
        assert mat == original


# ---------------------------------------------------------------------------
# reduce_row
# ---------------------------------------------------------------------------

class TestReduceRow:
    def test_numeric_factor(self):
        mat = Matrix([[1, 2], [3, 4]])
        mat.reduce_row(1, 3, 0, verbosity=0)  # R2 -= 3*R1
        assert mat[1, 0] == 0
        assert mat[1, 1] == -2

    def test_symbolic_factor(self, a):
        mat = Matrix([[1, 0], [a, 1]])
        mat.reduce_row(1, a, 0, verbosity=0)  # R2 -= a*R1
        assert mat[1, 0] == 0


# ---------------------------------------------------------------------------
# get_pivot_row
# ---------------------------------------------------------------------------

class TestGetPivotRow:
    def test_finds_correct_pivot_row(self):
        mat = Matrix([[0, 2, 3], [4, 5, 6], [7, 8, 9]])
        result = mat.get_pivot_row(col_idx=0, row_start_idx=0)
        assert result == 1  # first non-zero in col 0 is row 1

    def test_returns_none_when_no_pivot(self):
        mat = Matrix([[0, 0], [0, 0]])
        result = mat.get_pivot_row(col_idx=0, row_start_idx=0)
        assert result is None

    def test_start_row_respected(self):
        mat = Matrix([[1, 2], [3, 4]])
        result = mat.get_pivot_row(col_idx=0, row_start_idx=1)
        assert result == 1

    def test_all_zero_column_returns_none(self):
        mat = Matrix([[0, 1], [0, 2], [0, 3]])
        result = mat.get_pivot_row(col_idx=0, row_start_idx=0)
        assert result is None


# ---------------------------------------------------------------------------
# get_pivot_pos
# ---------------------------------------------------------------------------

class TestGetPivotPos:
    def test_upper_triangular_matrix(self):
        mat = Matrix([[1, 2, 3], [0, 4, 5], [0, 0, 6]])
        pivots = mat.get_pivot_pos()
        assert pivots == [(0, 0), (1, 1), (2, 2)]

    def test_rank_deficient_matrix(self):
        mat = Matrix([[1, 2, 3], [0, 0, 5], [0, 0, 0]])
        pivots = mat.get_pivot_pos()
        assert pivots == [(0, 0), (1, 2)]

    def test_empty_row_gives_fewer_pivots(self):
        mat = Matrix([[1, 0, 0], [0, 1, 0], [0, 0, 0]])
        pivots = mat.get_pivot_pos()
        assert len(pivots) == 2


# ---------------------------------------------------------------------------
# get_pivot_elements
# ---------------------------------------------------------------------------

class TestGetPivotElements:
    def test_values_at_pivot_positions(self):
        mat = Matrix([[2, 3, 4], [0, 5, 6], [0, 0, 7]])
        elements = mat.get_pivot_elements()
        assert elements == [2, 5, 7]

    def test_rank_deficient(self):
        mat = Matrix([[1, 2, 3], [0, 0, 5], [0, 0, 0]])
        elements = mat.get_pivot_elements()
        assert elements == [1, 5]
