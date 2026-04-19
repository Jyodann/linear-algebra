# GUI Enhancements Design — 2026-04-19

## Overview

Five improvements to the Linear Algebra Studio GUI:
1. Decimal input support for all symbolic operations
2. Chain matrix multiplication (up to 3 matrices, each optionally transposed or inverted)
3. Copy result to clipboard in parseable format
4. Calculation history sidebar drawer
5. Scrolling fix for long results

---

## 1. Decimal Input Support

**Problem:** SymPy's symbolic operations (diagonalize, eigenvals, eigenvects, nullspace, etc.) fail or produce incorrect output when matrix entries are Python floats.

**Fix:** In `app.py` `parse_matrix()`, after parsing, apply:
```python
A = A.applyfunc(lambda x: sym.nsimplify(x, rational=True))
```
This converts all float entries to exact rationals once at parse time. All downstream operations receive clean symbolic values. No per-operation changes needed.

**Scope:** Applies to all operations automatically.

---

## 2. Chain Matrix Multiplication

### UI (Frontend)

- New **"Arithmetic"** op-group added at the top of the ops panel (above Row Reduction), with a single **"Chain Multiply"** button
- Clicking "Chain Multiply" activates the operation and reveals a dedicated input area:
  - **M1** = existing Matrix A card (unchanged)
  - **M2** = new cardB-style card (always shown when op is active)
  - **M3** = optional, revealed by **"+ Add M3"** button; removed by **"× Remove M3"**
  - Each card header gets two small toggle buttons: **T** (transpose) and **⁻¹** (inverse)
    - Toggled state is visually indicated (active style matches accent color)
    - Multiple can be active simultaneously (e.g. both T and ⁻¹ = inverse of transpose)
    - Transform order: inverse first, then transpose (i.e. `(M^-1)^T`)
- M3 card is hidden by default; its modifier state resets when hidden

### Backend (`/api/process`)

New operation: `chain_multiply`

Request body fields:
```json
{
  "operation": "chain_multiply",
  "matrix":  "<M1 string>",
  "matrix2": "<M2 string>",
  "matrix3": "<M3 string, optional>",
  "mod1": "none|T|inv|inv_T",
  "mod2": "none|T|inv|inv_T",
  "mod3": "none|T|inv|inv_T"
}
```

Backend logic:
1. Parse each matrix, apply `nsimplify`
2. Apply modifier: `inv` → `.inv()`, `T` → `.T`, `inv_T` → `.inv().T`
3. Compute product: `M1_mod @ M2_mod` (and `@ M3_mod` if present)
4. Return LaTeX result + `raw` (see §3)

Result display: `\( M_1^{?} M_2^{?} M_3^{?} = \text{result} \)`

---

## 3. Copy Result

**UI:** A small **"Copy"** button appears in the top-right corner of the answer card after a successful result is computed. Hidden during computation and on error.

**What is copied (`raw` field):**
- Backend returns a `raw` field in every `/api/process` response alongside `result`
- `raw` is the result matrix formatted as `[v00 v01; v10 v11]` (Matrix.from_str compatible)
- For decompositions (PLU, QR, PDP, SVD): `raw` contains each component matrix on separate lines, labeled: `P=[...]\nL=[...]\nU=[...]`
- For scalar results (det, rank): `raw` is the scalar value as a string

**Interaction:**
- Click "Copy" → `navigator.clipboard.writeText(raw)`
- Button briefly shows **"✓"** (500ms) then reverts to "Copy"
- Button is hidden again when a new operation starts

---

## 4. History Sidebar Drawer

### State

JS array `history[]`, max 10 entries. Each entry:
```js
{
  op: "diagonalize",          // operation key
  label: "Diagonalization",   // human-readable label
  matrices: [                 // all matrices used
    { label: "A", value: "[1 2; 3 4]" },
    { label: "b", value: "[1; 0]" }     // if applicable
  ],
  result: "<html string>",    // rendered result HTML
  steps:  "<html string>",    // rendered steps HTML (may be empty)
  raw: "...",                 // copy-pasteable raw string
  timestamp: "14:32:01",      // HH:MM:SS
}
```

When a new result is successfully computed, prepend to `history[]`. If length > 10, pop the last entry.

### UI

**Trigger:** "History" button in the op-bar (right of status badge). Shows entry count badge when history is non-empty.

**Drawer:**
- Fixed-position overlay on the right side: `width: 320px`, `height: 100vh`, slides in with CSS `transform: translateX`
- Has its own scrollable body (`overflow-y: auto`) for the entry list
- **Header:** "History" title + "×" close button + "Clear" button
- **Entry list:** Each entry is a clickable card showing:
  - Operation name (bold) + timestamp (muted, right-aligned)
  - Matrix labels + truncated values for all matrices used (e.g. `A = [1 2; 3 4]`, max 1 line each)
- Clicking an entry:
  - Restores matrix string into Matrix A text input (switches to text mode)
  - Re-displays result and steps in the right panel
  - Closes the drawer
- Clicking the backdrop (outside drawer) closes the drawer
- Escape key closes the drawer

**Backdrop:** semi-transparent overlay behind drawer, same pattern as equiv modal.

---

## 5. Scrolling Fix

Three CSS changes in `style.css`:

| Selector | Current | Change | Reason |
|---|---|---|---|
| `.answer-card` | `overflow: hidden` | `overflow: visible` | Stops clipping tall/wide rendered math |
| `.result-body` | `align-items: center` | `align-items: flex-start` | Prevents flex centering from clipping tall content |
| `mjx-container` | `overflow-y: hidden` | `overflow-y: visible` | Stops tall matrices being clipped vertically |

The `.result-scroll` container already has `overflow-y: auto` so vertical scrolling is handled at that level. These changes remove inner clipping that fights it.

---

## Files Changed

| File | Changes |
|---|---|
| `src/gui/app.py` | `parse_matrix`: add nsimplify; all operation handlers: add `raw` to response; add `chain_multiply` operation |
| `src/gui/static/index.html` | Add Arithmetic op-group; M2/M3 cards with modifier toggles; History button; history drawer HTML |
| `src/gui/static/script.js` | Chain multiply UI logic; modifier toggle state; copy button; history state + drawer; update `runOperation` to save history |
| `src/gui/static/style.css` | Scrolling fixes; history drawer styles; copy button styles; modifier toggle button styles |

---

## Out of Scope

- Persistent history (localStorage)
- More than 3 matrices in chain multiply
- Undo/redo
