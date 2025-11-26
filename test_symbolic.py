from ma1522.symbolic import Matrix
import sympy as sym

try:
    # Test list of lists with strings
    data = [["sqrt(2)", "1"], ["0", "2^2"]]
    # Note: 2^2 in python is 0, but in sympy string parsing it might be XOR or Power depending on parser.
    # Sympy parsing usually treats ^ as XOR unless using specific transformations.
    # But wait, the user said "sqrt or ^". In standard math ^ is power.
    # Let's see how Matrix handles it.
    
    # We might need to preprocess or use from_str if we want ^ to be power.
    # Or rely on sympy's parse_expr.
    
    print("Attempting to create matrix from list of strings...")
    # Sympy Matrix constructor usually expects numbers or Expr objects, not strings directly?
    # Let's check.
    try:
        m = Matrix(data)
        print("Matrix created directly:", m)
    except Exception as e:
        print("Direct creation failed:", e)

    # Alternative: Convert strings to expressions first
    from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application, convert_xor
    
    transformations = (standard_transformations + (implicit_multiplication_application, convert_xor))
    
    data_expr = [[parse_expr(c, transformations=transformations) for c in row] for row in data]
    m2 = Matrix(data_expr)
    print("Matrix created from parsed exprs:", m2)
    
except Exception as e:
    print(f"Error: {e}")
