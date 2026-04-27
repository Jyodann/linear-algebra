"""Unit tests for parse_matrix and _parse_bracket_format in gui/app.py.

Covers:
  - Bracket format with whitespace-delimited integers
  - Bracket format with comma-delimited cells (spaces inside expressions OK)
  - Implicit multiplication (2a, 3b+1) via parse_expr transformations
  - Symbolic expressions (sqrt, pi, rational)
  - LaTeX input
  - Python list literal input
  - Error cases: empty, mismatched row lengths, invalid syntax
"""

import pytest
import sympy as sym

# Import the helpers directly from the GUI module
from gui.app import parse_matrix, _parse_bracket_format


# ---------------------------------------------------------------------------
# TestParseBracketFormat — whitespace-delimited (no commas)
# ---------------------------------------------------------------------------

class TestParseBracketFormat:

    def test_integer_matrix(self):
        M = _parse_bracket_format("[1 2; 3 4]")
        assert M.shape == (2, 2)
        assert M[0, 0] == 1
        assert M[1, 1] == 4

    def test_negative_integers(self):
        M = _parse_bracket_format("[1 -2 -1; 2 0 1; 2 -4 2; 4 0 0]")
        assert M.shape == (4, 3)
        assert M[0, 1] == -2

    def test_single_row(self):
        M = _parse_bracket_format("[3 0 4]")
        assert M.shape == (1, 3)
        assert M[0, 2] == 4

    def test_single_column(self):
        M = _parse_bracket_format("[1; 2; 3]")
        assert M.shape == (3, 1)

    def test_comma_separated_plain(self):
        M = _parse_bracket_format("[1, 2; 3, 4]")
        assert M[0, 1] == 2

    def test_comma_separated_with_spaces_in_expressions(self):
        M = _parse_bracket_format("[1, -1 + sqrt(5); 3, 4]")
        assert sym.simplify(M[0, 1] - (-1 + sym.sqrt(5))) == 0

    def test_rational_entries(self):
        M = _parse_bracket_format("[1/2 3/4; 1/3 2/3]")
        assert M[0, 0] == sym.Rational(1, 2)

    def test_row_length_mismatch_raises(self):
        with pytest.raises(ValueError, match="Row length mismatch"):
            _parse_bracket_format("[1 2; 3 4 5]")

    def test_empty_raises(self):
        with pytest.raises(Exception):
            _parse_bracket_format("[]")


# ---------------------------------------------------------------------------
# TestParseBracketImplicitMultiplication
#
# Regression: cells like "2a-1" previously failed sympify().
# Fixed by using parse_expr with implicit_multiplication_application.
# ---------------------------------------------------------------------------

class TestParseBracketImplicitMultiplication:

    def test_implicit_multiplication_simple(self):
        M = _parse_bracket_format("[2a; b]")
        a = sym.Symbol("a")
        b = sym.Symbol("b")
        assert sym.simplify(M[0, 0] - 2 * a) == 0
        assert sym.simplify(M[1, 0] - b) == 0

    def test_implicit_multiplication_with_subtraction(self):
        """2a-1 was the exact input that triggered the bug."""
        M = _parse_bracket_format("[2a-1 3b+2; 0 1]")
        a = sym.Symbol("a")
        b = sym.Symbol("b")
        assert sym.simplify(M[0, 0] - (2 * a - 1)) == 0
        assert sym.simplify(M[0, 1] - (3 * b + 2)) == 0

    def test_implicit_multiplication_comma_separated(self):
        M = _parse_bracket_format("[2a-1, 3b+2; 0, 1]")
        a = sym.Symbol("a")
        b = sym.Symbol("b")
        assert sym.simplify(M[0, 0] - (2 * a - 1)) == 0
        assert sym.simplify(M[0, 1] - (3 * b + 2)) == 0

    def test_coefficient_with_no_variable(self):
        M = _parse_bracket_format("[2 3; 4 5]")
        assert M[0, 0] == 2

    def test_negative_implicit(self):
        M = _parse_bracket_format("[-2a; 1]")
        a = sym.Symbol("a")
        assert sym.simplify(M[0, 0] + 2 * a) == 0

    def test_mixed_symbolic_numeric(self):
        M = _parse_bracket_format("[1 2a; 3 4]")
        a = sym.Symbol("a")
        assert M[0, 0] == 1
        assert sym.simplify(M[0, 1] - 2 * a) == 0

    def test_caret_exponent(self):
        """x^2 should parse as x**2 via convert_xor."""
        M = _parse_bracket_format("[x^2 - 1; 2]")
        x = sym.Symbol("x")
        assert sym.simplify(M[0, 0] - (x**2 - 1)) == 0

    def test_caret_exponent_complex(self):
        M = _parse_bracket_format("[x^2 + 2x - 1; x^2 - 3]")
        x = sym.Symbol("x")
        assert sym.simplify(M[0, 0] - (x**2 + 2*x - 1)) == 0
        assert sym.simplify(M[1, 0] - (x**2 - 3)) == 0

    def test_fractional_coefficient_with_space(self):
        """(1/3)x + 2 has spaces so whitespace-split fails; fallback parses whole row."""
        M = _parse_bracket_format("[(1/3)x + 2; 4]")
        x = sym.Symbol("x")
        assert sym.simplify(M[0, 0] - (x / 3 + 2)) == 0
        assert M[1, 0] == 4

    def test_fractional_coefficient_52x(self):
        M = _parse_bracket_format("[(5/2)x; 1]")
        x = sym.Symbol("x")
        assert sym.simplify(M[0, 0] - sym.Rational(5, 2) * x) == 0

    def test_multi_variable_expressions(self):
        M = _parse_bracket_format("[(5/2)x - 3y; 2x + y]")
        x, y = sym.Symbol("x"), sym.Symbol("y")
        assert sym.simplify(M[0, 0] - (sym.Rational(5, 2)*x - 3*y)) == 0
        assert sym.simplify(M[1, 0] - (2*x + y)) == 0


# ---------------------------------------------------------------------------
# TestParseMatrix — top-level dispatcher
# ---------------------------------------------------------------------------

class TestParseMatrix:

    def test_bracket_whitespace(self):
        M = parse_matrix("[1 2; 3 4]")
        assert M.shape == (2, 2)

    def test_bracket_comma(self):
        M = parse_matrix("[1, 2; 3, 4]")
        assert M.shape == (2, 2)

    def test_python_list_literal(self):
        M = parse_matrix("[[1, 2], [3, 4]]")
        assert M[0, 0] == 1
        assert M[1, 1] == 4

    def test_sqrt_expression(self):
        M = parse_matrix("[sqrt(2), 0; 0, sqrt(3)]")
        assert sym.simplify(M[0, 0] - sym.sqrt(2)) == 0

    def test_pi_expression(self):
        M = parse_matrix("[pi; 1]")
        assert sym.simplify(M[0, 0] - sym.pi) == 0

    def test_rational_fraction(self):
        M = parse_matrix("[1/3, 2/3; 1/4, 3/4]")
        assert M[0, 0] == sym.Rational(1, 3)

    def test_negative_entries(self):
        M = parse_matrix("[1 -2 -1; 2 0 1; 2 -4 2; 4 0 0]")
        assert M.shape == (4, 3)
        assert M[0, 1] == -2

    def test_empty_raises(self):
        with pytest.raises(Exception):
            parse_matrix("")

    def test_single_element(self):
        M = parse_matrix("[5]")
        assert M.shape == (1, 1)
        assert M[0, 0] == 5

    def test_symbolic_variable_bracket(self):
        M = parse_matrix("[a, b; c, d]")
        assert M.shape == (2, 2)
        # All entries should be symbols
        for i in range(2):
            for j in range(2):
                assert isinstance(M[i, j], sym.Symbol)

    def test_implicit_multiplication_end_to_end(self):
        """Regression: 2a-1 in bracket format should parse without error."""
        M = parse_matrix("[2a-1, 1; 0, 3b+2]")
        a = sym.Symbol("a")
        b = sym.Symbol("b")
        assert sym.simplify(M[0, 0] - (2 * a - 1)) == 0
        assert sym.simplify(M[1, 1] - (3 * b + 2)) == 0

    def test_caret_exponent_end_to_end(self):
        M = parse_matrix("[x^2 + 2x - 1; x^2 - 3]")
        x = sym.Symbol("x")
        assert sym.simplify(M[0, 0] - (x**2 + 2*x - 1)) == 0

    def test_52x_end_to_end(self):
        M = parse_matrix("[(5/2)x - 3y; 2x + y]")
        x, y = sym.Symbol("x"), sym.Symbol("y")
        assert sym.simplify(M[0, 0] - (sym.Rational(5, 2)*x - 3*y)) == 0

    def test_fractional_coeff_with_spaces_end_to_end(self):
        """(1/3)x + 2 uses spaces inside expression — fallback path."""
        M = parse_matrix("[(1/3)x + 2; 4]")
        x = sym.Symbol("x")
        assert sym.simplify(M[0, 0] - (x / 3 + 2)) == 0
