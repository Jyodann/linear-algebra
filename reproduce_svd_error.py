
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from ma1522.symbolic import Matrix
import traceback

def reproduce():
    try:
        # Matrix from the screenshot
        # Rows: 3, Cols: 4
        # 1, 0, 1, 0
        # -1, 2, 1, 2
        # 1, 1, 2, 1
        
        data = [
            [1, 0, 1, 0],
            [-1, 2, 1, 2],
            [1, 1, 2, 1]
        ]
        
        mat = Matrix(data)
        print(f"Matrix:\n{mat}")
        print(f"Shape: {mat.shape}")
        
        # We can't easily debug inside the library without modifying it or mocking.
        # But we can call super().singular_value_decomposition() manually to see what it returns.
        
        print("\nCalling SymPy SVD directly...")
        import sympy as sym
        sym_mat = sym.Matrix(data)
        U, S, V = sym_mat.singular_value_decomposition()
        print(f"SymPy U shape: {U.shape}")
        print(f"SymPy S shape: {S.shape}")
        print(f"SymPy V shape: {V.shape}")
        print(f"SymPy S:\n{S}")

        print("\nAttempting SVD via Matrix class...")
        U, S, V_T = mat.singular_value_decomposition()
        
        print("\nSVD Result:")
        print(f"U:\n{U}")
        print(f"S:\n{S}")
        print(f"V_T:\n{V_T}")
        
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    reproduce()
