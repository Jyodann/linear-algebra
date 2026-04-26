"""Integration tests for eigen-analysis: cpoly, is_diagonalizable,
eigenvects_associated, diagonalize, is_orthogonally_diagonalizable,
orthogonally_diagonalize, is_stochastic, equilibrium_vectors,
singular_value_decomposition, fast_svd."""

import pytest
import sympy as sym

from ma1522 import Matrix
from ma1522.custom_types import PDP, SVD, NumSVD


# ---------------------------------------------------------------------------
# TestCpoly
# ---------------------------------------------------------------------------

class TestCpoly:
    """Tests for Matrix.cpoly()."""

    def test_2x2_characteristic_polynomial_coefficients(self, mat_2x2):
        poly = mat_2x2.cpoly()
        p = sym.Poly(poly)
        assert p.all_coeffs() == [1, -5, -2]

    def test_diagonal_matrix_roots(self):
        diag = Matrix.diag(2, 5)
        poly = diag.cpoly()
        x = sym.Symbol("x", real=True)
        roots = sym.solve(poly, x)
        assert set(roots) == {2, 5}

    def test_3x3_identity_cpoly(self, identity_3):
        poly = identity_3.cpoly()
        x = sym.Symbol("x", real=True)
        roots = sym.solve(poly, x)
        # All roots should equal 1 (with multiplicity 3)
        assert all(r == 1 for r in roots)

    @pytest.mark.parametrize("entries,expected_roots", [
        ([3, 0, 0, 7], {3, 7}),
        ([-1, 0, 0, 4], {-1, 4}),
    ])
    def test_parametrized_diagonal_roots(self, entries, expected_roots):
        mat = Matrix([[entries[0], entries[1]], [entries[2], entries[3]]])
        poly = mat.cpoly()
        x = sym.Symbol("x", real=True)
        roots = set(sym.solve(poly, x))
        assert roots == expected_roots


# ---------------------------------------------------------------------------
# TestIsDiagonalizable
# ---------------------------------------------------------------------------

class TestIsDiagonalizable:
    """Tests for Matrix.is_diagonalizable()."""

    def test_diagonal_is_diagonalizable(self):
        mat = Matrix.diag(1, 2)
        assert mat.is_diagonalizable(verbosity=0) is True

    def test_identity_is_diagonalizable(self, identity_2):
        assert identity_2.is_diagonalizable(verbosity=0) is True

    def test_defective_is_not_diagonalizable(self):
        mat = Matrix([[1, 1], [0, 1]])
        assert mat.is_diagonalizable(verbosity=0) is False

    def test_distinct_eigenvalues_is_diagonalizable(self):
        mat = Matrix([[1, 2], [0, 3]])
        assert mat.is_diagonalizable(verbosity=0) is True

    @pytest.mark.parametrize("data,expected", [
        ([[2, 0], [0, 3]], True),
        ([[1, 1], [0, 1]], False),
        ([[1, 2], [0, 3]], True),
    ])
    def test_parametrized(self, data, expected):
        mat = Matrix(data)
        assert mat.is_diagonalizable(verbosity=0) is expected


# ---------------------------------------------------------------------------
# TestEigenvectsAssociated
# ---------------------------------------------------------------------------

class TestEigenvectsAssociated:
    """Tests for Matrix.eigenvects_associated(eigenvalue)."""

    def test_eigenvalue_2_gives_e1(self):
        mat = Matrix([[2, 0], [0, 3]])
        evects = mat.eigenvects_associated(2)
        assert evects is not None and len(evects) >= 1
        # eigenvector should be proportional to [1, 0]
        v = evects[0]
        assert sym.simplify(v[1, 0]) == 0
        assert v[0, 0] != 0

    def test_eigenvalue_3_gives_e2(self):
        mat = Matrix([[2, 0], [0, 3]])
        evects = mat.eigenvects_associated(3)
        assert evects is not None and len(evects) >= 1
        v = evects[0]
        assert sym.simplify(v[0, 0]) == 0
        assert v[1, 0] != 0

    def test_eigenvects_satisfy_eigenvalue_equation(self, mat_3x3):
        eigenvalues = list(mat_3x3.eigenvals().keys())
        for lam in eigenvalues:
            if not lam.is_real:
                continue
            evects = mat_3x3.eigenvects_associated(lam)
            if evects:
                for v in evects:
                    residual = mat_3x3 @ v - lam * v
                    assert sym.simplify(residual.norm()) == 0


# ---------------------------------------------------------------------------
# TestDiagonalize
# ---------------------------------------------------------------------------

class TestDiagonalize:
    """Tests for Matrix.diagonalize() — returns PDP."""

    def test_returns_pdp(self):
        mat = Matrix([[1, 2], [0, 3]])
        pdp = mat.diagonalize()
        assert isinstance(pdp, PDP)

    def test_reconstruction(self):
        mat = Matrix([[1, 2], [0, 3]])
        pdp = mat.diagonalize()
        reconstructed = pdp.P @ pdp.D @ pdp.P.inv()
        diff = sym.simplify((reconstructed - mat).norm())
        assert diff == 0

    def test_d_is_diagonal(self):
        mat = Matrix([[1, 2], [0, 3]])
        pdp = mat.diagonalize()
        D = pdp.D
        assert D[0, 1] == 0
        assert D[1, 0] == 0

    def test_p_is_invertible(self):
        mat = Matrix([[1, 2], [0, 3]])
        pdp = mat.diagonalize()
        assert pdp.P.det() != 0

    def test_2x2_mat_2x2_reconstruction(self, mat_2x2):
        pdp = mat_2x2.diagonalize()
        diff = sym.simplify((pdp.P @ pdp.D @ pdp.P.inv() - mat_2x2).norm())
        assert diff == 0


# ---------------------------------------------------------------------------
# TestIsOrthogonallyDiagonalizable
# ---------------------------------------------------------------------------

class TestIsOrthogonallyDiagonalizable:
    """Tests for Matrix.is_orthogonally_diagonalizable()."""

    def test_symmetric_is_orthog_diagonalizable(self):
        mat = Matrix([[2, 1], [1, 2]])
        assert mat.is_orthogonally_diagonalizable(verbosity=0) is True

    def test_non_symmetric_is_not(self, mat_2x2):
        # mat_2x2 = [[1,2],[3,4]] is not symmetric
        assert mat_2x2.is_orthogonally_diagonalizable(verbosity=0) is False

    def test_identity_is_orthog_diagonalizable(self, identity_2):
        assert identity_2.is_orthogonally_diagonalizable(verbosity=0) is True


# ---------------------------------------------------------------------------
# TestOrthogonallyDiagonalize
# ---------------------------------------------------------------------------

class TestOrthogonallyDiagonalize:
    """Tests for Matrix.orthogonally_diagonalize() — returns PDP."""

    def test_reconstruction(self):
        mat = Matrix([[2, 1], [1, 2]])
        pdp = mat.orthogonally_diagonalize(verbosity=0)
        assert isinstance(pdp, PDP)
        diff = sym.simplify((pdp.P @ pdp.D @ pdp.P.T - mat).norm())
        assert diff == 0

    def test_p_is_orthogonal(self, identity_2):
        mat = Matrix([[2, 1], [1, 2]])
        pdp = mat.orthogonally_diagonalize(verbosity=0)
        diff = sym.simplify((pdp.P.T @ pdp.P - identity_2).norm())
        assert diff == 0

    def test_d_is_diagonal(self):
        mat = Matrix([[2, 1], [1, 2]])
        pdp = mat.orthogonally_diagonalize(verbosity=0)
        assert pdp.D[0, 1] == 0
        assert pdp.D[1, 0] == 0


# ---------------------------------------------------------------------------
# TestIsStochastic
# ---------------------------------------------------------------------------

class TestIsStochastic:
    """Tests for Matrix.is_stochastic()."""

    def test_stochastic_fixture(self, stochastic_2x2):
        assert stochastic_2x2.is_stochastic(verbosity=0) is True

    def test_identity_is_stochastic(self, identity_2):
        assert identity_2.is_stochastic(verbosity=0) is True

    def test_non_stochastic_column_sum(self):
        mat = Matrix([[1, 0], [0, 2]])
        assert mat.is_stochastic(verbosity=0) is False

    def test_negative_entry_not_stochastic(self):
        mat = Matrix([[sym.Rational(3, 2), sym.Rational(1, 2)],
                      [sym.Rational(-1, 2), sym.Rational(1, 2)]])
        assert mat.is_stochastic(verbosity=0) is False


# ---------------------------------------------------------------------------
# TestEquilibriumVectors
# ---------------------------------------------------------------------------

class TestEquilibriumVectors:
    """Tests for Matrix.equilibrium_vectors()."""

    def test_equilibrium_satisfies_ax_equals_x(self, stochastic_2x2):
        eq = stochastic_2x2.equilibrium_vectors()
        diff = stochastic_2x2 @ eq - eq
        assert sym.simplify(diff.norm()) == 0

    def test_equilibrium_identity(self, identity_2):
        # For identity, any vector is equilibrium
        eq = identity_2.equilibrium_vectors()
        diff = identity_2 @ eq - eq
        assert diff.norm() == 0

    def test_equilibrium_is_matrix(self, stochastic_2x2):
        eq = stochastic_2x2.equilibrium_vectors()
        assert isinstance(eq, Matrix)


# ---------------------------------------------------------------------------
# TestSVD
# ---------------------------------------------------------------------------

class TestSVD:
    """Tests for Matrix.singular_value_decomposition() — returns SVD."""

    def test_returns_svd_type(self, mat_2x2):
        svd = mat_2x2.singular_value_decomposition(verbosity=0)
        assert isinstance(svd, SVD)

    def test_reconstruction(self, mat_2x2):
        svd = mat_2x2.singular_value_decomposition(verbosity=0)
        diff = (svd.U @ svd.S @ svd.V.T - mat_2x2).norm()
        assert sym.simplify(diff) == 0

    def test_u_is_orthogonal(self, mat_2x2, identity_2):
        svd = mat_2x2.singular_value_decomposition(verbosity=0)
        diff = sym.simplify((svd.U.T @ svd.U - identity_2).norm())
        assert diff == 0

    def test_v_is_orthogonal(self, mat_2x2, identity_2):
        svd = mat_2x2.singular_value_decomposition(verbosity=0)
        diff = sym.simplify((svd.V.T @ svd.V - identity_2).norm())
        assert diff == 0

    def test_s_is_diagonal_nonneg(self, mat_2x2):
        svd = mat_2x2.singular_value_decomposition(verbosity=0)
        S = svd.S
        assert S[0, 1] == 0
        assert S[1, 0] == 0
        for i in range(S.rows):
            assert S[i, i] >= 0

    def test_3x2_shapes(self):
        A = Matrix([[1, 0], [0, 1], [1, 1]])
        svd = A.singular_value_decomposition(verbosity=0)
        assert svd.U.rows == 3
        assert svd.V.rows == 2
        diff = (svd.U @ svd.S @ svd.V.T - A).norm()
        assert sym.simplify(diff) == 0


# ---------------------------------------------------------------------------
# TestFastSVD
# ---------------------------------------------------------------------------

class TestFastSVD:
    """Tests for Matrix.fast_svd(option='np') — returns NumSVD."""

    def test_returns_num_svd(self, mat_2x2):
        svd = mat_2x2.fast_svd(option="np", identify=False)
        assert isinstance(svd, NumSVD)

    def test_numeric_reconstruction(self, mat_2x2):
        svd = mat_2x2.fast_svd(option="np", identify=False)
        U, S, V = svd.U, svd.S, svd.V
        reconstructed = Matrix(U) @ Matrix(S) @ Matrix(V).T
        diff = (reconstructed - mat_2x2).norm()
        assert float(diff.evalf()) < 1e-9

    def test_shapes(self, mat_2x2):
        svd = mat_2x2.fast_svd(option="np", identify=False)
        U, S, V = svd.U, svd.S, svd.V
        assert U.shape[0] == 2
        assert S.shape == (2, 2)
        assert V.shape[0] == 2
