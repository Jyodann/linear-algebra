"""Tests for custom_types and utils modules.

Covers:
- Shape enum values
- PartGen, ScalarFactor, PLU, RREF, VecDecomp, QR, PDP, SVD, NumSVD, RREFCase
- _powerset, _is_zero, _textify, _wrap_latex, _standardise_symbol utility functions
"""

import numpy as np
import pytest
import sympy as sym
from unittest.mock import patch, MagicMock

from ma1522 import Matrix, PartGen, ScalarFactor, PLU, RREF, VecDecomp, QR, PDP, SVD, NumSVD, RREFCase
from ma1522.custom_types import Shape
from ma1522.utils import _powerset, _is_zero, _textify, _wrap_latex, _unwrap_latex, _standardise_symbol


# ---------------------------------------------------------------------------
# Shape enum
# ---------------------------------------------------------------------------

class TestShapeEnum:
    @pytest.mark.parametrize("shape, expected_value", [
        (Shape.SCALAR, "SCALAR"),
        (Shape.UPPER, "UPPER"),
        (Shape.LOWER, "LOWER"),
        (Shape.STRICT_UPPER, "STRICT_UPPER"),
        (Shape.STRICT_LOWER, "STRICT_LOWER"),
        (Shape.SYMMETRIC, "SYMMETRIC"),
        (Shape.DIAGONAL, "DIAGONAL"),
    ])
    def test_shape_values(self, shape, expected_value):
        assert shape.value == expected_value

    def test_shape_identity(self):
        """Each Shape member is the same object when accessed twice."""
        assert Shape.SCALAR is Shape.SCALAR
        assert Shape.UPPER is not Shape.LOWER


# ---------------------------------------------------------------------------
# PartGen
# ---------------------------------------------------------------------------

class TestPartGen:
    def test_construction_and_field_access(self):
        part = Matrix([[1, 0], [2, 0]])
        gen = Matrix([[0, 3], [0, 4]])
        pg = PartGen(part, gen)
        assert pg.part_sol == part
        assert pg.gen_sol == gen

    def test_eval_returns_sum(self):
        part = Matrix([[1, 0], [0, 1]])
        gen = Matrix([[0, 1], [1, 0]])
        pg = PartGen(part, gen)
        result = pg.eval()
        expected = Matrix([[1, 1], [1, 1]])
        assert result == expected

    def test_eval_with_concrete_values(self):
        part = Matrix([[1], [2]])
        gen = Matrix([[3], [4]])
        pg = PartGen(part, gen)
        assert pg.eval() == Matrix([[4], [6]])

    def test_latex_contains_both_parts(self):
        part = Matrix([[1, 0], [0, 1]])
        gen = Matrix([[0, 1], [1, 0]])
        pg = PartGen(part, gen)
        # _repr_latex_ uses the IPython printer (works without arguments)
        latex_str = pg._repr_latex_()
        assert isinstance(latex_str, str)
        assert len(latex_str) > 0
        assert "+" in latex_str

    def test_iter_unpacking(self):
        part = Matrix([[1], [0]])
        gen = Matrix([[0], [1]])
        pg = PartGen(part, gen)
        p, g = pg
        assert p == part
        assert g == gen

    def test_getitem_access(self):
        part = Matrix([[1, 0], [2, 0]])
        gen = Matrix([[0, 3], [0, 4]])
        pg = PartGen(part, gen)
        assert pg[0] == part
        assert pg[1] == gen


# ---------------------------------------------------------------------------
# ScalarFactor
# ---------------------------------------------------------------------------

class TestScalarFactor:
    def test_construction_fd(self):
        full = Matrix([[1, 1], [3, 2]])
        diag = Matrix.diag(6, 4)
        sf = ScalarFactor(diag=diag, full=full, order="FD")
        assert sf.full == full
        assert sf.diag == diag
        assert sf.order == "FD"

    def test_construction_df(self):
        full = Matrix([[1, 3], [1, 2]])
        diag = Matrix.diag(6, 4)
        sf = ScalarFactor(diag=diag, full=full, order="DF")
        assert sf.order == "DF"

    def test_eval_fd_is_full_at_diag(self):
        full = Matrix([[1, 1], [3, 2]])
        diag = Matrix.diag(6, 4)
        sf = ScalarFactor(diag=diag, full=full, order="FD")
        result = sf.eval()
        expected = full @ diag
        assert result == expected

    def test_eval_df_is_diag_at_full(self):
        full = Matrix([[1, 3], [1, 2]])
        diag = Matrix.diag(6, 4)
        sf = ScalarFactor(diag=diag, full=full, order="DF")
        result = sf.eval()
        expected = diag @ full
        assert result == expected

    def test_eval_reconstructs_column_factored_matrix(self):
        """scalar_factor(column=True) on [[6,4],[12,8]] returns full=[[1,1],[3,2]], diag=diag(6,4)."""
        mat = Matrix([[6, 4], [12, 8]])
        sf = mat.scalar_factor(column=True)
        assert sf.order == "FD"
        assert sf.full == Matrix([[1, 1], [2, 2]])
        assert sf.diag == Matrix.diag(6, 4)
        # Reconstruction: full @ diag == original
        assert sf.eval() == mat

    def test_eval_reconstructs_row_factored_matrix(self):
        """scalar_factor(column=False) on [[6,12],[4,8]] returns row factorization."""
        mat = Matrix([[6, 12], [4, 8]])
        sf = mat.scalar_factor(column=False)
        assert sf.order == "DF"
        assert sf.eval() == mat

    def test_iter_unpacking(self):
        full = Matrix([[1, 1], [3, 2]])
        diag = Matrix.diag(6, 4)
        sf = ScalarFactor(diag=diag, full=full, order="FD")
        d, f, o = sf
        assert d == diag
        assert f == full
        assert o == "FD"


# ---------------------------------------------------------------------------
# PLU
# ---------------------------------------------------------------------------

class TestPLU:
    def test_construction_and_field_access(self):
        P = Matrix([[1, 0], [0, 1]])
        L = Matrix([[1, 0], [2, 1]])
        U = Matrix([[3, 4], [0, 5]])
        plu = PLU(P, L, U)
        assert plu.P == P
        assert plu.L == L
        assert plu.U == U

    def test_eval_returns_p_at_l_at_u(self):
        P = Matrix([[1, 0], [0, 1]])
        L = Matrix([[1, 0], [2, 1]])
        U = Matrix([[3, 4], [0, 5]])
        plu = PLU(P, L, U)
        result = plu.eval()
        expected = P @ L @ U
        assert result == expected

    def test_eval_concrete(self):
        # [[3,4],[6,13]] = I @ [[1,0],[2,1]] @ [[3,4],[0,5]]
        A = Matrix([[3, 4], [6, 13]])
        P = Matrix.eye(2)
        L = Matrix([[1, 0], [2, 1]])
        U = Matrix([[3, 4], [0, 5]])
        plu = PLU(P, L, U)
        assert plu.eval() == A

    def test_iter_unpacking(self):
        P = Matrix.eye(2)
        L = Matrix.eye(2)
        U = Matrix([[1, 2], [0, 3]])
        plu = PLU(P, L, U)
        p, l, u = plu
        assert p == P
        assert l == L
        assert u == U


# ---------------------------------------------------------------------------
# RREF
# ---------------------------------------------------------------------------

class TestRREF:
    def test_construction_and_field_access(self):
        rref_mat = Matrix([[1, 0, 2], [0, 1, 3]])
        pivots = (0, 1)
        rref = RREF(rref_mat, pivots)
        assert rref.rref == rref_mat
        assert rref.pivots == pivots

    def test_eval_returns_rref_matrix(self):
        rref_mat = Matrix([[1, 0], [0, 1]])
        pivots = (0, 1)
        rref = RREF(rref_mat, pivots)
        assert rref.eval() == rref_mat

    def test_pivots_tuple_type(self):
        rref_mat = Matrix([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
        pivots = (0, 1, 2)
        rref = RREF(rref_mat, pivots)
        assert isinstance(rref.pivots, tuple)
        assert len(rref.pivots) == 3

    def test_iter_unpacking(self):
        rref_mat = Matrix([[1, 0], [0, 1]])
        pivots = (0, 1)
        rref = RREF(rref_mat, pivots)
        r, p = rref
        assert r == rref_mat
        assert p == pivots


# ---------------------------------------------------------------------------
# VecDecomp
# ---------------------------------------------------------------------------

class TestVecDecomp:
    def test_construction_and_field_access(self):
        proj = Matrix([[2], [0]])
        norm = Matrix([[0], [3]])
        vd = VecDecomp(proj, norm)
        assert vd.proj == proj
        assert vd.norm == norm

    def test_eval_returns_proj_plus_norm(self):
        proj = Matrix([[2], [0]])
        norm = Matrix([[0], [3]])
        vd = VecDecomp(proj, norm)
        result = vd.eval()
        expected = Matrix([[2], [3]])
        assert result == expected

    def test_iter_unpacking(self):
        proj = Matrix([[1], [0]])
        norm = Matrix([[0], [1]])
        vd = VecDecomp(proj, norm)
        p, n = vd
        assert p == proj
        assert n == norm


# ---------------------------------------------------------------------------
# QR
# ---------------------------------------------------------------------------

class TestQR:
    def test_construction_and_field_access(self):
        Q = Matrix([[1, 0], [0, 1]])
        R = Matrix([[2, 3], [0, 4]])
        qr = QR(Q, R)
        assert qr.Q == Q
        assert qr.R == R

    def test_eval_returns_q_at_r(self):
        Q = Matrix([[1, 0], [0, 1]])
        R = Matrix([[2, 3], [0, 4]])
        qr = QR(Q, R)
        assert qr.eval() == Q @ R

    def test_tuple_unpacking(self):
        Q = Matrix([[1, 0], [0, 1]])
        R = Matrix([[5, 6], [0, 7]])
        qr = QR(Q, R)
        q_out, r_out = qr
        assert q_out == Q
        assert r_out == R


# ---------------------------------------------------------------------------
# PDP
# ---------------------------------------------------------------------------

class TestPDP:
    def test_construction_and_field_access(self):
        P = Matrix([[1, 1], [0, 1]])
        D = Matrix.diag(2, 3)
        pdp = PDP(P, D)
        assert pdp.P == P
        assert pdp.D == D

    def test_eval_returns_p_d_p_inv(self):
        # Use identity so P_inv = P and eval = D
        P = Matrix.eye(2)
        D = Matrix.diag(2, 3)
        pdp = PDP(P, D)
        assert pdp.eval() == D

    def test_iter_unpacking(self):
        P = Matrix.eye(2)
        D = Matrix.diag(4, 5)
        pdp = PDP(P, D)
        p, d = pdp
        assert p == P
        assert d == D


# ---------------------------------------------------------------------------
# SVD
# ---------------------------------------------------------------------------

class TestSVD:
    def test_construction_and_field_access(self):
        U = Matrix([[1, 0], [0, 1]])
        S = Matrix.diag(3, 2)
        V = Matrix([[1, 0], [0, 1]])
        svd = SVD(U, S, V)
        assert svd.U == U
        assert svd.S == S
        assert svd.V == V

    def test_eval_returns_u_s_vt(self):
        U = Matrix([[1, 0], [0, 1]])
        S = Matrix.diag(3, 2)
        V = Matrix([[1, 0], [0, 1]])
        svd = SVD(U, S, V)
        result = svd.eval()
        expected = U @ S @ V.T
        assert result == expected

    def test_eval_nontrivial(self):
        # Verify U @ S @ V.T gives back a specific matrix
        U = Matrix([[1, 0], [0, 1]])
        S = Matrix([[5, 0], [0, 3]])
        V = Matrix([[1, 0], [0, 1]])
        svd = SVD(U, S, V)
        assert svd.eval() == Matrix([[5, 0], [0, 3]])

    def test_iter_unpacking(self):
        U = Matrix.eye(2)
        S = Matrix.diag(1, 2)
        V = Matrix.eye(2)
        svd = SVD(U, S, V)
        u, s, v = svd
        assert u == U
        assert s == S
        assert v == V


# ---------------------------------------------------------------------------
# NumSVD
# ---------------------------------------------------------------------------

class TestNumSVD:
    def test_construction_and_field_access(self):
        U = np.eye(2)
        S = np.diag([3.0, 1.0])
        V = np.eye(2)
        numsvd = NumSVD(U, S, V)
        assert np.allclose(numsvd.U, U)
        assert np.allclose(numsvd.S, S)
        assert np.allclose(numsvd.V, V)

    def test_eval_returns_numpy_product(self):
        U = np.array([[1.0, 0.0], [0.0, 1.0]])
        S = np.diag([3.0, 2.0])
        V = np.array([[1.0, 0.0], [0.0, 1.0]])
        numsvd = NumSVD(U, S, V)
        result = numsvd.eval()
        expected = U @ S @ V.T
        assert np.allclose(result, expected)

    def test_named_tuple_access_by_index(self):
        U = np.eye(3)
        S = np.diag([5.0, 3.0, 1.0])
        V = np.eye(3)
        numsvd = NumSVD(U, S, V)
        assert np.allclose(numsvd[0], U)
        assert np.allclose(numsvd[1], S)
        assert np.allclose(numsvd[2], V)


# ---------------------------------------------------------------------------
# _powerset
# ---------------------------------------------------------------------------

class TestPowerset:
    def test_three_elements(self):
        result = list(_powerset([1, 2, 3]))
        expected = [(), (1,), (2,), (3,), (1, 2), (1, 3), (2, 3), (1, 2, 3)]
        assert result == expected

    def test_empty_input(self):
        result = list(_powerset([]))
        assert result == [()]

    def test_single_element(self):
        result = list(_powerset([42]))
        assert result == [(), (42,)]

    def test_two_elements(self):
        result = list(_powerset([1, 2]))
        assert result == [(), (1,), (2,), (1, 2)]

    def test_length_is_2_to_n(self):
        for n in range(5):
            items = list(range(n))
            result = list(_powerset(items))
            assert len(result) == 2 ** n


# ---------------------------------------------------------------------------
# _is_zero
# ---------------------------------------------------------------------------

class TestIsZero:
    def test_literal_zero(self):
        assert _is_zero(0) is True

    def test_literal_one(self):
        assert _is_zero(1) is False

    def test_literal_nonzero_integer(self):
        assert _is_zero(5) is False
        assert _is_zero(-3) is False

    def test_symbolic_expression_simplifies_to_zero(self):
        a = sym.Symbol("a")
        assert _is_zero(a * 0) is True

    def test_symbolic_sum_is_zero(self):
        # sym.Integer(0) is zero
        assert _is_zero(sym.Integer(0)) is True

    def test_symbolic_constant_nonzero(self):
        # sympy Number 1 is not zero
        assert _is_zero(sym.Integer(1)) is False

    def test_fraction_denominator_one(self):
        # Denominator of an integer fraction is 1, which is nonzero
        n, d = sym.fraction(sym.Integer(5))
        assert _is_zero(d) is False

    def test_symbolic_variable_can_be_zero(self):
        # A free symbol can be zero (no assumption)
        a = sym.Symbol("a")
        assert _is_zero(a) is True


# ---------------------------------------------------------------------------
# RREFCase
# ---------------------------------------------------------------------------

class TestRREFCase:
    def test_construction_and_fields(self):
        rc = RREFCase(
            conditions={"a": 0},
            excluded=[{"b": 0}],
            rref=Matrix.eye(2),
            pivots=(0, 1),
            free_params=0,
            is_consistent=True,
        )
        assert rc.eval() == Matrix.eye(2)
        assert "RREFCase" in rc._latex()

    def test_consistency_flag(self):
        rc = RREFCase(
            conditions={},
            excluded=[],
            rref=Matrix([[1, 0, 0], [0, 1, 0]]),
            pivots=(0, 1),
            free_params=0,
            is_consistent=True,
        )
        assert rc.is_consistent is True

    def test_free_params(self):
        rc = RREFCase(
            conditions={},
            excluded=[],
            rref=Matrix([[1, 0, 0], [0, 0, 0]]),
            pivots=(0,),
            free_params=1,
            is_consistent=True,
        )
        assert rc.free_params == 1


# ---------------------------------------------------------------------------
# Utils — _textify, _wrap_latex, _standardise_symbol
# ---------------------------------------------------------------------------

class TestTextify:
    def test_underscore_escaping(self):
        assert _textify("hello_world") == r"\text{hello\_world}"

    def test_no_underscore(self):
        assert _textify("Simple") == r"\text{Simple}"


class TestLatexWrapping:
    def test_wrap(self):
        assert _wrap_latex("x") == "$x$"

    def test_unwrap_single_dollar(self):
        assert _unwrap_latex("$x$") == "x"

    def test_unwrap_double_dollar(self):
        assert _unwrap_latex("$$x$$") == "x"

    def test_unwrap_none(self):
        assert _unwrap_latex(None) == ""


class TestStandardiseSymbol:
    def test_subscript_digits(self):
        symbols = {sym.Symbol("x1"), sym.Symbol("y2")}
        std = _standardise_symbol(symbols)
        std_names = [str(s) for s in std]
        assert "x_1" in std_names
        assert "y_2" in std_names


class TestIPythonUtils:
    def test_is_ipython_false_on_name_error(self):
        from ma1522.utils import _is_IPython
        with patch("IPython.core.getipython.get_ipython", side_effect=NameError):
            assert _is_IPython() is False

    def test_is_ipython_true_for_zmq_shell(self):
        from ma1522.utils import _is_IPython
        with patch("IPython.core.getipython.get_ipython") as mock_get:
            mock_shell = MagicMock()
            mock_shell.__class__.__name__ = "ZMQInteractiveShell"
            mock_get.return_value = mock_shell
            assert _is_IPython() is True

    def test_is_ipython_false_for_unknown_shell(self):
        from ma1522.utils import _is_IPython
        with patch("IPython.core.getipython.get_ipython") as mock_get:
            mock_shell = MagicMock()
            mock_shell.__class__.__name__ = "SomeOtherShell"
            mock_get.return_value = mock_shell
            assert _is_IPython() is False
