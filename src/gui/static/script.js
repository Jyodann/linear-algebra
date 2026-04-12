/* ─────────────────────────────────────────────────────────────────────────
   Linear Algebra Studio — Frontend Controller
   ───────────────────────────────────────────────────────────────────────── */

'use strict';

/* ── Operation metadata ─────────────────────────────────────────────────── */
const OP_LABELS = {
  rref:             'RREF',
  ref:              'REF (with steps)',
  lu:               'LU Decomposition',
  qr:               'QR Decomposition',
  svd:              'SVD',
  gram_schmidt:     'Gram-Schmidt Orthogonalization',
  det:              'Determinant',
  inv:              'Inverse',
  rank:             'Rank & Nullity',
  eigenvals:        'Eigenvalues',
  eigenvects:       'Eigenvectors',
  diagonalize:      'Diagonalization',
  orth_diagonalize: 'Orthogonal Diagonalization',
  nullspace:        'Nullspace',
  colspace:         'Column Space',
  orth_complement:  'Orthogonal Complement',
  col_constraints:  'Column Constraints',
  extend_basis:     'Extend Basis',
  solve:            'Solve Ax = b',
  least_squares:    'Least Squares',
  projection:       'Projection [A|b]',
  intersect:        'Intersect Subspaces',
  transition:       'Transition Matrix',
  eval_cases:       'Evaluate Cases',
  find_cases:       'Find Cases',
};

/* ── State ──────────────────────────────────────────────────────────────── */
const state = {
  rowsA: 2,
  colsA: 2,
  rowsB: 2,
  colsB: 1,
  textModeA: false,       // grid vs textarea
  secondaryMode: null,    // null | 'rhs' | 'rhs-optional' | 'matrix2'
  stepsCollapsed: false,
  activeOp: null,
  currentAbort: null,     // AbortController for in-flight request
};

/* ── DOM references ─────────────────────────────────────────────────────── */
const $ = id => document.getElementById(id);

const els = {
  rowsA:       $('rowsA'),
  colsA:       $('colsA'),
  updateA:     $('updateA'),
  clearA:      $('clearA'),
  gridA:       $('gridA'),
  textWrapA:   $('textWrapA'),
  textA:       $('textA'),
  toggleModeA: $('toggleModeA'),
  cardB:       $('cardB'),
  labelB:      $('labelB'),
  dimCtrlB:    $('dimCtrlB'),
  rowsB:       $('rowsB'),
  colsB:       $('colsB'),
  updateB:     $('updateB'),
  gridB:       $('gridB'),
  hintB:       $('hintB'),
  opLabel:     $('opLabel'),
  statusBadge: $('statusBadge'),
  cancelBtn:   $('cancelBtn'),
  resultDisplay: $('resultDisplay'),
  stepsCard:   $('stepsCard'),
  stepsBody:   $('stepsBody'),
  toggleSteps: $('toggleSteps'),
  toggleStepsLabel: $('toggleStepsLabel'),
  equivBtn:    $('equivBtn'),
  equivModal:  $('equivModal'),
  closeModal:  $('closeModal'),
  equivCategory: $('equivCategory'),
  equivProps:  $('equivProps'),
  equivList:   $('equivList'),
};

/* ─────────────────────────────────────────────────────────────────────────
   Grid helpers
   ───────────────────────────────────────────────────────────────────────── */

/**
 * Build a rows×cols input grid inside `containerId`.
 * Sets grid-template-columns and appends .grid-cell inputs.
 */
function createGrid(containerId, rows, cols) {
  const container = $(containerId);
  container.innerHTML = '';
  container.style.gridTemplateColumns = `repeat(${cols}, auto)`;

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const input = document.createElement('input');
      input.type = 'text';
      input.className = 'grid-cell';
      input.dataset.row = r;
      input.dataset.col = c;
      input.placeholder = '0';
      input.autocomplete = 'off';
      input.spellcheck = false;

      // Tab navigation: move right across the row, then down
      input.addEventListener('keydown', e => {
        if (e.key === 'Enter') {
          e.preventDefault();
          const next = container.querySelector(
            `[data-row="${r + 1}"][data-col="${c}"]`
          );
          if (next) next.focus();
        }
      });

      container.appendChild(input);
    }
  }
}

/**
 * Read a grid into "[v00 v01; v10 v11]" format (Matrix.from_str compatible).
 * Empty cells become "0".
 */
function readGrid(containerId, rows, cols) {
  const container = $(containerId);
  const rowStrs = [];
  for (let r = 0; r < rows; r++) {
    const row = [];
    for (let c = 0; c < cols; c++) {
      const cell = container.querySelector(`[data-row="${r}"][data-col="${c}"]`);
      const val = (cell && cell.value.trim()) ? cell.value.trim() : '0';
      row.push(val);
    }
    rowStrs.push(row.join(' '));
  }
  return '[' + rowStrs.join('; ') + ']';
}

/** Zero-fill all grid cells. */
function clearGrid(containerId) {
  const container = $(containerId);
  container.querySelectorAll('.grid-cell').forEach(c => { c.value = ''; });
}

/* ─────────────────────────────────────────────────────────────────────────
   Matrix A management
   ───────────────────────────────────────────────────────────────────────── */

function initGridA() {
  createGrid('gridA', state.rowsA, state.colsA);
}

function syncDimInputsA() {
  els.rowsA.value = state.rowsA;
  els.colsA.value = state.colsA;
}

function applyDimA() {
  const r = parseInt(els.rowsA.value, 10);
  const c = parseInt(els.colsA.value, 10);
  if (!r || !c || r < 1 || c < 1) return;
  state.rowsA = r;
  state.colsA = c;
  createGrid('gridA', r, c);

  // Auto-sync rowsB when in rhs / rhs-optional mode
  if (state.secondaryMode === 'rhs' || state.secondaryMode === 'rhs-optional') {
    state.rowsB = r;
    els.rowsB.value = r;
    createGrid('gridB', state.rowsB, state.colsB);
  }
}

/** Read the current Matrix A string (grid or text mode). */
function getMatrixA() {
  if (state.textModeA) {
    return els.textA.value.trim();
  }
  return readGrid('gridA', state.rowsA, state.colsA);
}

/** Toggle grid ↔ text mode for Matrix A. */
function toggleTextModeA() {
  state.textModeA = !state.textModeA;
  if (state.textModeA) {
    // Capture current grid values into textarea (from_str format)
    const gridStr = readGrid('gridA', state.rowsA, state.colsA);
    els.textA.value = gridStr;
    els.gridA.classList.add('hidden');
    els.textWrapA.classList.remove('hidden');
  } else {
    els.textWrapA.classList.add('hidden');
    els.gridA.classList.remove('hidden');
  }
}

/* ─────────────────────────────────────────────────────────────────────────
   Secondary input (cardB)
   ───────────────────────────────────────────────────────────────────────── */

/**
 * Show or hide cardB, configuring label, hint, and dim controls.
 * mode: null | 'rhs' | 'rhs-optional' | 'matrix2'
 */
function showSecondary(mode) {
  if (state.secondaryMode === mode) {
    if (mode === 'rhs' || mode === 'rhs-optional') {
      if (state.rowsB !== state.rowsA) {
        state.rowsB = state.rowsA;
        createGrid('gridB', state.rowsB, state.colsB);
      }
    }
    return; // Fast path: already showing correctly
  }
  
  state.secondaryMode = mode;

  if (!mode) {
    els.cardB.classList.add('hidden');
    return;
  }

  els.cardB.classList.remove('hidden');

  if (mode === 'rhs') {
    els.labelB.textContent = 'Vector b';
    els.hintB.textContent = '';
    els.dimCtrlB.classList.add('hidden');
    state.rowsB = state.rowsA;
    state.colsB = 1;
    createGrid('gridB', state.rowsB, state.colsB);
  } else if (mode === 'rhs-optional') {
    els.labelB.textContent = 'Vector b (optional)';
    els.hintB.textContent = 'Leave empty to use the zero vector.';
    els.dimCtrlB.classList.add('hidden');
    state.rowsB = state.rowsA;
    state.colsB = 1;
    createGrid('gridB', state.rowsB, state.colsB);
  } else if (mode === 'matrix2') {
    els.labelB.textContent = 'Matrix B';
    els.hintB.textContent = '';
    els.dimCtrlB.classList.remove('hidden');
    els.rowsB.value = state.rowsB;
    els.colsB.value = state.colsB;
    createGrid('gridB', state.rowsB, state.colsB);
  }
}

function applyDimB() {
  const r = parseInt(els.rowsB.value, 10);
  const c = parseInt(els.colsB.value, 10);
  if (!r || !c || r < 1 || c < 1) return;
  state.rowsB = r;
  state.colsB = c;
  createGrid('gridB', r, c);
}

/** Read secondary input. Returns null if mode is rhs-optional and all cells empty. */
function getSecondaryValue() {
  const mode = state.secondaryMode;
  if (!mode) return null;

  const raw = readGrid('gridB', state.rowsB, state.colsB);

  if (mode === 'rhs-optional') {
    const container = els.gridB;
    const allEmpty = Array.from(
      container.querySelectorAll('.grid-cell')
    ).every(c => c.value.trim() === '');
    if (allEmpty) return null;
  }

  return raw;
}

/* ─────────────────────────────────────────────────────────────────────────
   Status badge
   ───────────────────────────────────────────────────────────────────────── */

function setStatus(state_) {
  const badge = els.statusBadge;
  badge.className = 'status-badge';
  const cancelBtn = $('cancelBtn');
  switch (state_) {
    case 'ready':
      badge.classList.add('status-ready');
      badge.textContent = 'Ready';
      if (cancelBtn) cancelBtn.classList.add('hidden');
      break;
    case 'computing':
      badge.classList.add('status-computing');
      badge.textContent = 'Computing…';
      if (cancelBtn) cancelBtn.classList.remove('hidden');
      break;
    case 'done':
      badge.classList.add('status-done');
      badge.textContent = 'Done ✓';
      if (cancelBtn) cancelBtn.classList.add('hidden');
      break;
    case 'error':
      badge.classList.add('status-error');
      badge.textContent = 'Error';
      if (cancelBtn) cancelBtn.classList.add('hidden');
      break;
  }
}

/* ─────────────────────────────────────────────────────────────────────────
   Result & steps rendering
   ───────────────────────────────────────────────────────────────────────── */

function renderResult(html) {
  els.resultDisplay.innerHTML = html;
  if (window.MathJax && MathJax.typesetPromise) {
    MathJax.typesetPromise([els.resultDisplay]).catch(console.error);
  }
}

function renderSteps(html) {
  els.stepsBody.innerHTML = html;
  els.stepsCard.classList.remove('hidden');

  // Restore collapse state
  if (state.stepsCollapsed) {
    els.stepsBody.classList.add('hidden');
    els.toggleStepsLabel.textContent = '\u25b8 Expand';
  } else {
    els.stepsBody.classList.remove('hidden');
    els.toggleStepsLabel.textContent = '\u25be Collapse';
  }

  if (window.MathJax && MathJax.typesetPromise) {
    MathJax.typesetPromise([els.stepsBody]).catch(console.error);
  }
}

function clearSteps() {
  els.stepsCard.classList.add('hidden');
  els.stepsBody.innerHTML = '';
}

/* ─────────────────────────────────────────────────────────────────────────
   Core operation handler
   ───────────────────────────────────────────────────────────────────────── */

async function runOperation(op, needs) {
  // Abort any in-flight request
  if (state.currentAbort) {
    state.currentAbort.abort();
    state.currentAbort = null;
  }

  // Update active state
  document.querySelectorAll('.op-btn').forEach(b => b.classList.remove('active'));
  const btn = document.querySelector(`[data-op="${op}"]`);
  if (btn) btn.classList.add('active');

  state.activeOp = op;
  els.opLabel.textContent = OP_LABELS[op] || op;
  setStatus('computing');
  clearSteps();
  renderResult('<p class="placeholder">Computing…</p>');

  // Show / hide secondary input
  showSecondary(needs || null);

  // Build request body
  const body = { operation: op };

  const matA = getMatrixA();
  if (!matA) {
    setStatus('error');
    renderResult('<div class="error-message">Matrix A is empty.</div>');
    return;
  }
  body.matrix = matA;

  if (needs === 'rhs' || needs === 'rhs-optional') {
    const rhsVal = getSecondaryValue();
    if (rhsVal) body.rhs = rhsVal;
  } else if (needs === 'matrix2') {
    const m2 = readGrid('gridB', state.rowsB, state.colsB);
    body.matrix2 = m2;
  }

  // Create abort controller for this request
  const controller = new AbortController();
  state.currentAbort = controller;

  try {
    const resp = await fetch('/api/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    state.currentAbort = null;
    const data = await resp.json();

    if (data.error) {
      setStatus('error');
      renderResult(`<div class="error-message">Error: ${escapeHtml(data.error)}</div>`);
      return;
    }

    setStatus('done');
    renderResult(data.result || '<span class="placeholder">No result returned.</span>');

    if (data.steps && data.steps.trim()) {
      renderSteps(data.steps);
    }
  } catch (err) {
    state.currentAbort = null;
    if (err.name === 'AbortError') {
      // User cancelled — reset cleanly
      setStatus('ready');
      renderResult('<p class="placeholder">Cancelled. Select an operation from the left panel.</p>');
      clearSteps();
    } else {
      setStatus('error');
      renderResult(`<div class="error-message">Network error: ${escapeHtml(err.message)}</div>`);
    }
  }
}

/* ─────────────────────────────────────────────────────────────────────────
   Equivalent Statements modal
   ───────────────────────────────────────────────────────────────────────── */

async function openEquivModal() {
  const matA = getMatrixA();
  if (!matA) {
    alert('Please enter a matrix first.');
    return;
  }

  // Reset modal content
  els.equivCategory.textContent = 'Loading…';
  els.equivProps.innerHTML = '';
  els.equivList.innerHTML = '';
  els.equivModal.classList.remove('hidden');

  try {
    const resp = await fetch('/api/equivalent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ matrix: matA }),
    });

    const data = await resp.json();

    if (data.error) {
      els.equivCategory.textContent = 'Error';
      els.equivList.innerHTML = `<li><div class="error-message">${escapeHtml(data.error)}</div></li>`;
      return;
    }

    // Category
    els.equivCategory.textContent = data.category || '';

    // Property tags
    const p = data.properties || {};
    const tagDefs = [
      { cls: 'tag-rows',    label: `rows = ${p.rows}` },
      { cls: 'tag-cols',    label: `cols = ${p.cols}` },
      { cls: 'tag-rank',    label: `rank = ${p.rank}` },
      { cls: 'tag-nullity', label: `nullity = ${p.nullity}` },
    ];
    els.equivProps.innerHTML = tagDefs
      .map(t => `<span class="prop-tag ${t.cls}">${escapeHtml(t.label)}</span>`)
      .join('');

    // Statements list
    const stmts = data.statements || [];
    els.equivList.innerHTML = stmts
      .map(s => `<li>${s}</li>`)
      .join('');

    // Re-typeset LaTeX inside modal
    if (window.MathJax && MathJax.typesetPromise) {
      MathJax.typesetPromise([els.equivModal]).catch(console.error);
    }
  } catch (err) {
    els.equivCategory.textContent = 'Network error';
    els.equivList.innerHTML = `<li><div class="error-message">${escapeHtml(err.message)}</div></li>`;
  }
}

function closeEquivModal() {
  els.equivModal.classList.add('hidden');
}

/* ─────────────────────────────────────────────────────────────────────────
   Utility
   ───────────────────────────────────────────────────────────────────────── */

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/* ─────────────────────────────────────────────────────────────────────────
   Initialisation
   ───────────────────────────────────────────────────────────────────────── */

function init() {
  // 1. Apply op-group colors from data-color attribute (CSS attr() not yet
  //    supported for custom properties in all browsers)
  document.querySelectorAll('.op-group').forEach(g => {
    g.style.setProperty('--group-color', g.dataset.color);
  });

  // 2. Build Matrix A grid
  initGridA();

  // 3. Matrix A dim controls
  els.updateA.addEventListener('click', applyDimA);
  els.rowsA.addEventListener('keydown', e => e.key === 'Enter' && applyDimA());
  els.colsA.addEventListener('keydown', e => e.key === 'Enter' && applyDimA());
  els.clearA.addEventListener('click', () => clearGrid('gridA'));

  // 4. Text mode toggle for Matrix A
  els.toggleModeA.addEventListener('click', toggleTextModeA);

  // 5. Matrix B dim controls
  els.updateB.addEventListener('click', applyDimB);
  els.rowsB.addEventListener('keydown', e => e.key === 'Enter' && applyDimB());
  els.colsB.addEventListener('keydown', e => e.key === 'Enter' && applyDimB());

  // 6. Operation buttons
  document.querySelectorAll('.op-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const op = btn.dataset.op;
      const needs = btn.dataset.needs;  // '', 'rhs', 'rhs-optional', 'matrix2'
      if (!op) return;
      runOperation(op, needs);
    });
  });

  // 7. Steps collapse toggle
  els.toggleSteps.addEventListener('click', () => {
    state.stepsCollapsed = !state.stepsCollapsed;
    if (state.stepsCollapsed) {
      els.stepsBody.classList.add('hidden');
      els.toggleStepsLabel.textContent = '\u25b8 Expand';
    } else {
      els.stepsBody.classList.remove('hidden');
      els.toggleStepsLabel.textContent = '\u25be Collapse';
    }
  });

  // 8. Equivalent statements
  els.equivBtn.addEventListener('click', openEquivModal);
  els.closeModal.addEventListener('click', closeEquivModal);

  // 9. Cancel button
  const cancelBtn = $('cancelBtn');
  if (cancelBtn) {
    cancelBtn.addEventListener('click', () => {
      if (state.currentAbort) {
        state.currentAbort.abort();
        state.currentAbort = null;
      }
    });
  }

  // Close modal on backdrop click
  els.equivModal.addEventListener('click', e => {
    if (e.target === els.equivModal) closeEquivModal();
  });

  // Close modal on Escape
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && !els.equivModal.classList.contains('hidden')) {
      closeEquivModal();
    }
  });
}

// Kick off once DOM is ready
document.addEventListener('DOMContentLoaded', init);
