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
  projection:       'Projection onto Col(A)',
  intersect:        'Intersect Subspaces',
  transition:       'Transition Matrix',
  eval_cases:       'Evaluate Cases',
  find_cases:       'Find Cases',
  chain_multiply:   'Chain Multiply',
};

/* ── Status badge config ────────────────────────────────────────────────── */
const STATUS_CONFIG = {
  ready:     { cls: 'status-ready',     text: 'Ready',       cancel: false },
  computing: { cls: 'status-computing', text: 'Computing\u2026', cancel: true  },
  done:      { cls: 'status-done',      text: 'Done \u2713', cancel: false },
  error:     { cls: 'status-error',     text: 'Error',       cancel: false },
};

/* ── State ──────────────────────────────────────────────────────────────── */
const state = {
  rowsA: 2, colsA: 2,
  rowsB: 2, colsB: 1,
  rowsC: 2, colsC: 2,
  textModeA: false,
  textModeB: false,
  textModeC: false,
  autoLinkSize: true,
  secondaryMode: null,    // null | 'rhs' | 'rhs-optional' | 'matrix2' | 'chain'
  stepsCollapsed: false,
  activeOp: null,
  activeNeeds: null,
  currentAbort: null,
  lastRaw: null,
  chain: {
    modA: { T: false, inv: false },
    modB: { T: false, inv: false },
    modC: { T: false, inv: false },
    showM3: false,
  },
};

/* ── Undo / Redo ────────────────────────────────────────────────────────── */
const _undoStack = [];
const _redoStack = [];
const UNDO_MAX = 50;

/** Capture full snapshot of all three grids + dims. */
function captureSnapshot() {
  return {
    rowsA: state.rowsA, colsA: state.colsA, cellsA: saveGrid('gridA'),
    rowsB: state.rowsB, colsB: state.colsB, cellsB: saveGrid('gridB'),
    rowsC: state.rowsC, colsC: state.colsC, cellsC: saveGrid('gridC'),
  };
}

/** Push current state onto undo stack and clear redo. */
function pushUndo() {
  _undoStack.push(captureSnapshot());
  if (_undoStack.length > UNDO_MAX) _undoStack.shift();
  _redoStack.length = 0;
  updateUndoButtons();
}

function applySnapshot(snap) {
  // Matrix A
  state.rowsA = snap.rowsA; state.colsA = snap.colsA;
  els.rowsA.value = snap.rowsA; els.colsA.value = snap.colsA;
  createGrid('gridA', snap.rowsA, snap.colsA);
  restoreGrid('gridA', snap.cellsA);
  // Matrix B (only if card visible)
  state.rowsB = snap.rowsB; state.colsB = snap.colsB;
  if (els.rowsB) els.rowsB.value = snap.rowsB;
  if (els.colsB) els.colsB.value = snap.colsB;
  createGrid('gridB', snap.rowsB, snap.colsB);
  restoreGrid('gridB', snap.cellsB);
  // Matrix C (only if card visible)
  state.rowsC = snap.rowsC; state.colsC = snap.colsC;
  if (els.rowsC) els.rowsC.value = snap.rowsC;
  if (els.colsC) els.colsC.value = snap.colsC;
  createGrid('gridC', snap.rowsC, snap.colsC);
  restoreGrid('gridC', snap.cellsC);
}

function performUndo() {
  if (!_undoStack.length) return;
  _redoStack.push(captureSnapshot());
  applySnapshot(_undoStack.pop());
  updateUndoButtons();
}

function performRedo() {
  if (!_redoStack.length) return;
  _undoStack.push(captureSnapshot());
  applySnapshot(_redoStack.pop());
  updateUndoButtons();
}

function updateUndoButtons() {
  if (els.undoBtn) els.undoBtn.disabled = _undoStack.length === 0;
  if (els.redoBtn) els.redoBtn.disabled = _redoStack.length === 0;
}

/* ── DOM references ─────────────────────────────────────────────────────── */
const $ = id => document.getElementById(id);

const els = {
  rowsA:            $('rowsA'),
  colsA:            $('colsA'),
  updateA:          $('updateA'),
  clearA:           $('clearA'),
  gridA:            $('gridA'),
  textWrapA:        $('textWrapA'),
  textA:            $('textA'),
  toggleModeA:      $('toggleModeA'),
  cardB:            $('cardB'),
  labelB:           $('labelB'),
  dimCtrlB:         $('dimCtrlB'),
  rowsB:            $('rowsB'),
  colsB:            $('colsB'),
  updateB:          $('updateB'),
  gridB:            $('gridB'),
  textWrapB:        $('textWrapB'),
  textB:            $('textB'),
  toggleModeB:      $('toggleModeB'),
  hintB:            $('hintB'),
  cardC:            $('cardC'),
  gridC:            $('gridC'),
  textWrapC:        $('textWrapC'),
  textC:            $('textC'),
  toggleModeC:      $('toggleModeC'),
  rowsC:            $('rowsC'),
  colsC:            $('colsC'),
  updateC:          $('updateC'),
  opLabel:          $('opLabel'),
  computeBtn:       $('computeBtn'),
  statusBadge:      $('statusBadge'),
  cancelBtn:        $('cancelBtn'),
  answerShimmer:    $('answerShimmer'),
  resultDisplay:    $('resultDisplay'),
  stepsCard:        $('stepsCard'),
  stepsBody:        $('stepsBody'),
  toggleSteps:      $('toggleSteps'),
  toggleStepsLabel: $('toggleStepsLabel'),
  equivBtn:         $('equivBtn'),
  equivModal:       $('equivModal'),
  closeModal:       $('closeModal'),
  equivCategory:    $('equivCategory'),
  equivProps:       $('equivProps'),
  equivList:        $('equivList'),
  modsA:    $('modsA'),
  modSegA:  $('modSegA'),
  modsB:    $('modsB'),
  modSegB:  $('modSegB'),
  modsC:    $('modsC'),
  modSegC:  $('modSegC'),
  addM3Btn:        $('addM3Btn'),
  copyBtn:         $('copyBtn'),
  inputSummary:    $('inputSummary'),
  inputDisplay:    $('inputDisplay'),
  helpBtn:         $('helpBtn'),
  helpModal:       $('helpModal'),
  closeHelpModal:  $('closeHelpModal'),
  historyBtn:      $('historyBtn'),
  historyCount:    $('historyCount'),
  historyDrawer:   $('historyDrawer'),
  historyBackdrop: $('historyBackdrop'),
  clearHistoryBtn: $('clearHistoryBtn'),
  closeHistoryBtn: $('closeHistoryBtn'),
  historyList:     $('historyList'),
  settingsBtn:     $('settingsBtn'),
  settingsPopover: $('settingsPopover'),
  settingsClose:   $('settingsClose'),
  darkToggle:      $('darkToggle'),
  autoLinkToggle:  $('autoLinkToggle'),
  undoBtn:         $('undoBtn'),
  redoBtn:         $('redoBtn'),
};

/* ─────────────────────────────────────────────────────────────────────────
   Backend parse helper
   ───────────────────────────────────────────────────────────────────────── */

/** Call /api/parse; returns {rows, cols, cells} or null on error. */
async function fetchParse(text) {
  try {
    const resp = await fetch('/api/parse', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ matrix: text }),
    });
    const data = await resp.json();
    if (data.error) return null;
    return data;
  } catch {
    return null;
  }
}

/**
 * Populate a grid with parsed cell data from fetchParse.
 * Updates state dims. Does NOT switch text/grid mode.
 */
function populateGrid(gridId, data, rowKey, colKey, rowInput, colInput) {
  state[rowKey] = data.rows;
  state[colKey] = data.cols;
  if (rowInput) rowInput.value = data.rows;
  if (colInput) colInput.value = data.cols;
  createGrid(gridId, data.rows, data.cols);
  const container = $(gridId);
  data.cells.forEach((row, r) => {
    row.forEach((val, c) => {
      const cell = container.querySelector(`[data-row="${r}"][data-col="${c}"]`);
      if (cell) cell.value = val;
    });
  });
}

/* ─────────────────────────────────────────────────────────────────────────
   Grid helpers
   ───────────────────────────────────────────────────────────────────────── */

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

      input.addEventListener('keydown', e => {
        const dirs = {
          Enter:      [1,  0],
          ArrowDown:  [1,  0],
          ArrowUp:    [-1, 0],
          ArrowRight: [0,  1],
          ArrowLeft:  [0, -1],
        };
        const delta = dirs[e.key];
        if (!delta) return;

        // Horizontal arrows only navigate when cursor is at the boundary
        if (e.key === 'ArrowLeft') {
          if (input.selectionStart !== 0 || input.selectionEnd !== 0) return;
        }
        if (e.key === 'ArrowRight') {
          const end = input.value.length;
          if (input.selectionStart !== end || input.selectionEnd !== end) return;
        }

        const next = container.querySelector(
          `[data-row="${r + delta[0]}"][data-col="${c + delta[1]}"]`
        );
        if (next) { e.preventDefault(); next.focus(); }
      });

      // Snapshot before edit so Cmd+Z can revert the value
      input.addEventListener('focus', () => { input._preVal = input.value; });
      input.addEventListener('blur', () => {
        if (input.value !== input._preVal) {
          pushUndo();
          saveSession();
        }
      });

      container.appendChild(input);
    }
  }
}

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

function clearGrid(containerId) {
  const container = $(containerId);
  container.querySelectorAll('.grid-cell').forEach(c => { c.value = ''; });
}

/** Snapshot all non-empty cell values. Returns Map keyed by "row,col". */
function saveGrid(containerId) {
  const saved = new Map();
  const container = $(containerId);
  container.querySelectorAll('.grid-cell').forEach(cell => {
    const v = cell.value.trim();
    if (v) saved.set(`${cell.dataset.row},${cell.dataset.col}`, v);
  });
  return saved;
}

/** Restore cell values from a Map keyed by "row,col". */
function restoreGrid(containerId, saved) {
  if (!saved || saved.size === 0) return;
  const container = $(containerId);
  saved.forEach((val, key) => {
    const [row, col] = key.split(',');
    const cell = container.querySelector(`[data-row="${row}"][data-col="${col}"]`);
    if (cell) cell.value = val;
  });
}

/* ─────────────────────────────────────────────────────────────────────────
   Matrix A management
   ───────────────────────────────────────────────────────────────────────── */

function initGridA() { createGrid('gridA', state.rowsA, state.colsA); }

function syncDimInputsA() {
  els.rowsA.value = state.rowsA;
  els.colsA.value = state.colsA;
}

async function applyDimA() {
  const r = parseInt(els.rowsA.value, 10);
  const c = parseInt(els.colsA.value, 10);
  if (!r || !c || r < 1 || c < 1) return;

  pushUndo();

  // Exit text mode: parse textarea, switch to grid
  if (state.textModeA) {
    const text = els.textA.value.trim();
    if (text) {
      const data = await fetchParse(text);
      if (data) populateGrid('gridA', data, 'rowsA', 'colsA', els.rowsA, els.colsA);
    }
    state.textModeA = false;
    els.textWrapA.classList.add('hidden');
    els.gridA.classList.remove('hidden');
  }

  const saved = saveGrid('gridA');
  state.rowsA = r;
  state.colsA = c;
  createGrid('gridA', r, c);
  restoreGrid('gridA', saved);

  applyAutoLink('A');
}

function getMatrixA() {
  if (state.textModeA) return els.textA.value.trim();
  return readGrid('gridA', state.rowsA, state.colsA);
}

/** Toggle grid ↔ text mode for Matrix A.
 *  text→grid: parse via backend and populate grid cells. */
async function toggleTextModeA() {
  if (state.textModeA) {
    // text → grid: parse and populate
    const text = els.textA.value.trim();
    if (text) {
      const data = await fetchParse(text);
      if (data) {
        populateGrid('gridA', data, 'rowsA', 'colsA', els.rowsA, els.colsA);
      }
    }
    state.textModeA = false;
    els.textWrapA.classList.add('hidden');
    els.gridA.classList.remove('hidden');
  } else {
    // grid → text
    state.textModeA = true;
    els.textA.value = readGrid('gridA', state.rowsA, state.colsA);
    els.gridA.classList.add('hidden');
    els.textWrapA.classList.remove('hidden');
    els.textA.focus();
  }
}

/* ─────────────────────────────────────────────────────────────────────────
   Matrix B management
   ───────────────────────────────────────────────────────────────────────── */

function getMatrixB() {
  if (state.textModeB) return els.textB.value.trim();
  return readGrid('gridB', state.rowsB, state.colsB);
}

async function toggleTextModeB() {
  if (state.textModeB) {
    const text = els.textB.value.trim();
    if (text) {
      const data = await fetchParse(text);
      if (data) {
        populateGrid('gridB', data, 'rowsB', 'colsB', els.rowsB, els.colsB);
      }
    }
    state.textModeB = false;
    els.textWrapB.classList.add('hidden');
    els.gridB.classList.remove('hidden');
  } else {
    state.textModeB = true;
    els.textB.value = readGrid('gridB', state.rowsB, state.colsB);
    els.gridB.classList.add('hidden');
    els.textWrapB.classList.remove('hidden');
    els.textB.focus();
  }
}

/* ─────────────────────────────────────────────────────────────────────────
   Matrix C management
   ───────────────────────────────────────────────────────────────────────── */

function getMatrixC() {
  if (state.textModeC) return els.textC.value.trim();
  return readGrid('gridC', state.rowsC, state.colsC);
}

async function toggleTextModeC() {
  if (state.textModeC) {
    const text = els.textC.value.trim();
    if (text) {
      const data = await fetchParse(text);
      if (data) {
        populateGrid('gridC', data, 'rowsC', 'colsC', els.rowsC, els.colsC);
      }
    }
    state.textModeC = false;
    els.textWrapC.classList.add('hidden');
    els.gridC.classList.remove('hidden');
  } else {
    state.textModeC = true;
    els.textC.value = readGrid('gridC', state.rowsC, state.colsC);
    els.gridC.classList.add('hidden');
    els.textWrapC.classList.remove('hidden');
    els.textC.focus();
  }
}

/* ─────────────────────────────────────────────────────────────────────────
   Secondary input (cardB)
   ───────────────────────────────────────────────────────────────────────── */

function showSecondary(mode) {
  if (state.secondaryMode === 'chain' && mode !== 'chain') {
    configureForChain(false);
  }

  // Reset text mode for B when mode changes
  if (state.secondaryMode !== mode && state.textModeB) {
    state.textModeB = false;
    els.textWrapB.classList.add('hidden');
    els.gridB.classList.remove('hidden');
  }

  if (state.secondaryMode === mode) {
    if (mode === 'rhs' || mode === 'rhs-optional') {
      if (state.rowsB !== state.rowsA) {
        state.rowsB = state.rowsA;
        createGrid('gridB', state.rowsB, state.colsB);
      }
    }
    return;
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
  } else if (mode === 'chain') {
    els.labelB.textContent = 'Matrix M2';
    els.hintB.textContent = '';
    els.dimCtrlB.classList.remove('hidden');
    els.rowsB.value = state.rowsB;
    els.colsB.value = state.colsB;
    createGrid('gridB', state.rowsB, state.colsB);
    configureForChain(true);
  }
}

async function applyDimB() {
  const r = parseInt(els.rowsB.value, 10);
  const c = parseInt(els.colsB.value, 10);
  if (!r || !c || r < 1 || c < 1) return;

  pushUndo();

  // Exit text mode: parse textarea, switch to grid
  if (state.textModeB) {
    const text = els.textB.value.trim();
    if (text) {
      const data = await fetchParse(text);
      if (data) populateGrid('gridB', data, 'rowsB', 'colsB', els.rowsB, els.colsB);
    }
    state.textModeB = false;
    els.textWrapB.classList.add('hidden');
    els.gridB.classList.remove('hidden');
  }

  const saved = saveGrid('gridB');
  state.rowsB = r;
  state.colsB = c;
  createGrid('gridB', r, c);
  restoreGrid('gridB', saved);

  applyAutoLink('B');
}

/**
 * Enforce dimensional constraints between A and B after one side changed.
 * source: 'A' | 'B'
 * Only fires when state.autoLinkSize is true and the constrained dim differs.
 */
function applyAutoLink(source) {
  if (!state.autoLinkSize) return;
  const mode = state.secondaryMode;
  if (!mode) return;

  if (mode === 'rhs' || mode === 'rhs-optional') {
    // Constraint: rows(A) === rows(b)
    if (source === 'A') {
      if (state.rowsB !== state.rowsA) {
        const savedB = saveGrid('gridB');
        state.rowsB = state.rowsA;
        els.rowsB.value = state.rowsA;
        createGrid('gridB', state.rowsB, state.colsB);
        restoreGrid('gridB', savedB);
      }
    } else if (source === 'B') {
      if (state.rowsA !== state.rowsB) {
        const savedA = saveGrid('gridA');
        state.rowsA = state.rowsB;
        els.rowsA.value = state.rowsB;
        createGrid('gridA', state.rowsA, state.colsA);
        restoreGrid('gridA', savedA);
      }
    }
  } else if (mode === 'matrix2' || mode === 'chain') {
    // Constraint: cols(A) === rows(B)
    if (source === 'A') {
      if (state.rowsB !== state.colsA) {
        const savedB = saveGrid('gridB');
        state.rowsB = state.colsA;
        els.rowsB.value = state.colsA;
        createGrid('gridB', state.rowsB, state.colsB);
        restoreGrid('gridB', savedB);
      }
    } else if (source === 'B') {
      if (state.colsA !== state.rowsB) {
        const savedA = saveGrid('gridA');
        state.colsA = state.rowsB;
        els.colsA.value = state.rowsB;
        createGrid('gridA', state.rowsA, state.colsA);
        restoreGrid('gridA', savedA);
      }
    }
  }
}

/** Read secondary input. Returns null if mode is rhs-optional and all cells empty. */
function getSecondaryValue() {
  const mode = state.secondaryMode;
  if (!mode) return null;

  const raw = getMatrixB();

  if (mode === 'rhs-optional') {
    // Check if text mode has content, or grid is all empty
    if (state.textModeB) {
      if (!raw) return null;
    } else {
      const allEmpty = Array.from(
        els.gridB.querySelectorAll('.grid-cell')
      ).every(c => c.value.trim() === '');
      if (allEmpty) return null;
    }
  }

  return raw;
}

/* ─────────────────────────────────────────────────────────────────────────
   Status badge
   ───────────────────────────────────────────────────────────────────────── */

function setStatus(s) {
  const cfg = STATUS_CONFIG[s];
  if (!cfg) return;
  els.statusBadge.className = `status-badge ${cfg.cls}`;
  els.statusBadge.textContent = cfg.text;
  els.cancelBtn.classList.toggle('hidden', !cfg.cancel);
}

/* ─────────────────────────────────────────────────────────────────────────
   Result & steps rendering
   ───────────────────────────────────────────────────────────────────────── */

function showShimmer() {
  els.answerShimmer.classList.remove('hidden');
  els.resultDisplay.classList.add('hidden');
  els.resultDisplay.innerHTML = '';
  els.copyBtn.classList.add('hidden');
  els.inputSummary.classList.add('hidden');
  els.inputDisplay.innerHTML = '';
  els.copyBtn.textContent = 'Copy';
  state.lastRaw = null;
}

function hideShimmer() {
  els.answerShimmer.classList.add('hidden');
  els.resultDisplay.classList.remove('hidden');
}

async function typesetMath(container) {
  if (window.MathJax && MathJax.typesetPromise) {
    await MathJax.typesetPromise([container]).catch(console.error);
  }
}

async function renderResult(html) {
  els.resultDisplay.innerHTML = html;
  await typesetMath(els.resultDisplay);
  hideShimmer();
}

function applyStepsVisibility() {
  if (state.stepsCollapsed) {
    els.stepsBody.classList.add('hidden');
    els.toggleStepsLabel.textContent = 'Show steps';
    els.toggleSteps.setAttribute('aria-expanded', 'false');
  } else {
    els.stepsBody.classList.remove('hidden');
    els.toggleStepsLabel.textContent = 'Hide steps';
    els.toggleSteps.setAttribute('aria-expanded', 'true');
  }
}

function renderSteps(html) {
  els.stepsBody.innerHTML = html;
  els.stepsCard.classList.remove('hidden');
  applyStepsVisibility();
  typesetMath(els.stepsBody);
}

function clearSteps() {
  els.stepsCard.classList.add('hidden');
  els.stepsBody.innerHTML = '';
}

/* ─────────────────────────────────────────────────────────────────────────
   Chain multiply helpers
   ───────────────────────────────────────────────────────────────────────── */

function getChainMod(segEl) {
  if (!segEl) return 'none';
  const active = segEl.querySelector('.mod-seg-btn.active');
  return active ? active.dataset.mod : 'none';
}

function resetChainMods() {
  [els.modSegA, els.modSegB, els.modSegC].forEach(seg => {
    if (!seg) return;
    seg.querySelectorAll('.mod-seg-btn').forEach(b => b.classList.remove('active'));
    const noneBtn = seg.querySelector('[data-mod="none"]');
    if (noneBtn) noneBtn.classList.add('active');
  });
}

function configureForChain(active) {
  if (active) {
    els.modsA.classList.remove('hidden');
    els.modsB.classList.remove('hidden');
    els.addM3Btn.classList.remove('hidden');
  } else {
    els.modsA.classList.add('hidden');
    els.modsB.classList.add('hidden');
    els.addM3Btn.classList.add('hidden');
    els.addM3Btn.classList.remove('m3-active');
    els.addM3Btn.innerHTML = '<svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true"><path d="M6 1v10M1 6h10" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg> Add third matrix';
    els.cardC.classList.add('hidden');
    state.chain.showM3 = false;
    resetChainMods();
  }
}

/* ─────────────────────────────────────────────────────────────────────────
   Select operation (without running)
   ───────────────────────────────────────────────────────────────────────── */

function selectOp(op, needs) {
  opBtns.forEach(b => b.classList.remove('active'));
  const btn = document.querySelector(`[data-op="${op}"]`);
  if (btn) btn.classList.add('active');

  state.activeOp = op;
  state.activeNeeds = needs || null;
  els.opLabel.textContent = OP_LABELS[op] || op;
  showSecondary(needs || null);
  els.computeBtn.disabled = false;
  els.computeBtn.title = `Run ${OP_LABELS[op] || op}`;
}

/* ─────────────────────────────────────────────────────────────────────────
   Core operation handler
   ───────────────────────────────────────────────────────────────────────── */

let _opGeneration = 0;

async function runOperation() {
  const op    = state.activeOp;
  const needs = state.activeNeeds;

  if (!op) return;

  if (state.currentAbort) {
    state.currentAbort.abort();
    state.currentAbort = null;
  }
  const myGen = ++_opGeneration;

  setStatus('computing');
  clearSteps();
  showShimmer();
  els.computeBtn.disabled = true;

  const body = { operation: op };

  const matA = getMatrixA();
  if (!matA) {
    setStatus('error');
    await renderResult('<div class="error-message">Matrix A is empty.</div>');
    els.computeBtn.disabled = false;
    return;
  }
  body.matrix = matA;

  if (needs === 'rhs' || needs === 'rhs-optional') {
    const rhsVal = getSecondaryValue();
    if (rhsVal) body.rhs = rhsVal;
  } else if (needs === 'matrix2') {
    body.matrix2 = getMatrixB();
  } else if (needs === 'chain') {
    body.matrix2 = getMatrixB();
    if (state.chain.showM3) {
      body.matrix3 = getMatrixC();
    }
    body.mod1 = getChainMod(els.modSegA);
    body.mod2 = getChainMod(els.modSegB);
    body.mod3 = getChainMod(els.modSegC);
  }

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
    if (myGen !== _opGeneration) return;
    const data = await resp.json();

    els.computeBtn.disabled = false;

    if (data.error) {
      setStatus('error');
      await renderResult(`<div class="error-message">Could not compute \u2014 ${escapeHtml(data.error)}</div>`);
      return;
    }

    setStatus('done');
    await renderResult(data.result || '<span class="placeholder">No result returned.</span>');
    state.lastRaw = data.raw || null;
    els.copyBtn.classList.toggle('hidden', !state.lastRaw);

    if (data.input_latex) {
      els.inputDisplay.innerHTML = data.input_latex;
      els.inputSummary.classList.remove('hidden');
      await typesetMath(els.inputDisplay);
    }

    // Record history
    const histMatrices = [{ label: 'A', value: getMatrixA() }];
    if (needs === 'rhs' || needs === 'rhs-optional') {
      const rhsVal = getSecondaryValue();
      if (rhsVal) histMatrices.push({ label: 'b', value: rhsVal });
    } else if (needs === 'matrix2') {
      histMatrices.push({ label: 'B', value: getMatrixB() });
    } else if (needs === 'chain') {
      histMatrices.push({ label: 'M2', value: getMatrixB() });
      if (state.chain.showM3) histMatrices.push({ label: 'M3', value: getMatrixC() });
    }
    addToHistory(op, OP_LABELS[op] || op, histMatrices, data.result || '', data.steps || '', data.raw || '');

    if (data.steps && data.steps.trim()) renderSteps(data.steps);

  } catch (err) {
    state.currentAbort = null;
    els.computeBtn.disabled = false;
    if (err.name === 'AbortError') {
      if (myGen !== _opGeneration) return;
      els.resultDisplay.innerHTML = '<p class="placeholder">Cancelled. Select an operation from the left panel.</p>';
      hideShimmer();
      setStatus('ready');
      clearSteps();
    } else {
      if (myGen !== _opGeneration) return;
      setStatus('error');
      await renderResult(`<div class="error-message">Network error: ${escapeHtml(err.message)}</div>`);
    }
  }
}

/* ─────────────────────────────────────────────────────────────────────────
   Equivalent Statements modal
   ───────────────────────────────────────────────────────────────────────── */

let _closeTimer   = null;
let _modalOpener  = null;
let _modalFocusable = [];

function getFocusable(container) {
  return Array.from(container.querySelectorAll(
    'a[href], button:not([disabled]), input:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
  ));
}

async function openEquivModal() {
  const matA = getMatrixA();
  if (!matA) { alert('Please enter a matrix first.'); return; }

  clearTimeout(_closeTimer);
  _modalOpener = document.activeElement;

  els.equivCategory.textContent = 'Loading\u2026';
  els.equivProps.innerHTML = '';
  els.equivList.innerHTML = '';

  els.equivModal.classList.remove('hidden');
  requestAnimationFrame(() =>
    requestAnimationFrame(() => {
      els.equivModal.classList.add('modal-visible');
      _modalFocusable = getFocusable(els.equivModal);
      if (_modalFocusable.length) _modalFocusable[0].focus();
    })
  );

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

    els.equivCategory.textContent = data.category || '';
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
    els.equivList.innerHTML = (data.statements || []).map(s => `<li>${s}</li>`).join('');
    typesetMath(els.equivModal);
  } catch (err) {
    els.equivCategory.textContent = 'Network error';
    els.equivList.innerHTML = `<li><div class="error-message">${escapeHtml(err.message)}</div></li>`;
  }
}

function openHelpModal() {
  els.helpModal.classList.remove('hidden');
  requestAnimationFrame(() => requestAnimationFrame(() => {
    els.helpModal.classList.add('modal-visible');
  }));
}

function closeHelpModal() {
  els.helpModal.classList.remove('modal-visible');
  setTimeout(() => els.helpModal.classList.add('hidden'), 200);
}

function closeEquivModal() {
  clearTimeout(_closeTimer);
  els.equivModal.classList.remove('modal-visible');
  _closeTimer = setTimeout(() => {
    els.equivModal.classList.add('hidden');
    if (_modalOpener && typeof _modalOpener.focus === 'function') _modalOpener.focus();
    _modalOpener = null;
  }, 200);
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
   History
   ───────────────────────────────────────────────────────────────────────── */

const _history = [];
const HISTORY_MAX = 50;

function _timestamp() {
  return new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function updateHistoryCount() {
  const n = _history.length;
  els.historyCount.textContent = n;
  els.historyCount.classList.toggle('hidden', n === 0);
}

function addToHistory(op, label, matrices, result, steps, raw) {
  _history.unshift({ op, label, matrices, result, steps, raw, timestamp: _timestamp() });
  if (_history.length > HISTORY_MAX) _history.pop();
  updateHistoryCount();
}

function renderHistoryList() {
  if (_history.length === 0) {
    els.historyList.innerHTML = '<p class="placeholder" style="padding:1rem;text-align:center;font-size:0.8rem">No history yet</p>';
    return;
  }
  els.historyList.innerHTML = _history.map((entry, i) => {
    const matPreview = entry.matrices.map(m => {
      const val = m.value.length > 22 ? m.value.slice(0, 22) + '\u2026' : m.value;
      return `<div>${escapeHtml(m.label)} = ${escapeHtml(val)}</div>`;
    }).join('');
    return `<div class="history-entry" data-idx="${i}">
      <div class="history-entry-header">
        <span class="history-entry-op">${escapeHtml(entry.label)}</span>
        <span class="history-entry-time">${entry.timestamp}</span>
      </div>
      <div class="history-entry-matrices">${matPreview}</div>
    </div>`;
  }).join('');

  els.historyList.querySelectorAll('.history-entry').forEach(el => {
    el.addEventListener('click', () => restoreHistory(_history[parseInt(el.dataset.idx, 10)]));
  });
}

function openHistoryDrawer() {
  renderHistoryList();
  els.historyBackdrop.classList.remove('hidden');
  requestAnimationFrame(() => els.historyDrawer.classList.add('drawer-open'));
}

function closeHistoryDrawer() {
  els.historyDrawer.classList.remove('drawer-open');
  setTimeout(() => els.historyBackdrop.classList.add('hidden'), 250);
}

/* ─────────────────────────────────────────────────────────────────────────
   Settings popover
   ───────────────────────────────────────────────────────────────────────── */

function openSettings() {
  els.settingsPopover.classList.remove('hidden');
  els.settingsBtn.classList.add('active');
}

function closeSettings() {
  els.settingsPopover.classList.add('hidden');
  els.settingsBtn.classList.remove('active');
}

function applyDarkMode(dark) {
  document.body.dataset.theme = dark ? 'dark' : '';
  els.darkToggle.setAttribute('aria-checked', dark ? 'true' : 'false');
  localStorage.setItem('la-studio-dark', dark ? '1' : '0');
}

function applyAutoLinkPref(on) {
  state.autoLinkSize = on;
  els.autoLinkToggle.setAttribute('aria-checked', on ? 'true' : 'false');
  localStorage.setItem('la-studio-autolink', on ? '1' : '0');
}

function restoreHistory(entry) {
  // Restore Matrix A in text mode
  if (!state.textModeA) {
    state.textModeA = true;
    els.gridA.classList.add('hidden');
    els.textWrapA.classList.remove('hidden');
  }
  els.textA.value = entry.matrices[0].value;

  // Restore Matrix B if present
  if (entry.matrices.length > 1 && entry.matrices[1].label !== 'M3') {
    if (!state.textModeB) {
      state.textModeB = true;
      els.gridB.classList.add('hidden');
      els.textWrapB.classList.remove('hidden');
    }
    els.textB.value = entry.matrices[1].value;
  }

  els.resultDisplay.innerHTML = entry.result || '';
  typesetMath(els.resultDisplay);
  els.inputSummary.classList.add('hidden');
  els.inputDisplay.innerHTML = '';
  hideShimmer();

  if (entry.steps && entry.steps.trim()) renderSteps(entry.steps);
  else clearSteps();

  state.lastRaw = entry.raw || null;
  els.copyBtn.classList.toggle('hidden', !state.lastRaw);

  opBtns.forEach(b => b.classList.remove('active'));
  state.activeOp = entry.op;
  state.activeNeeds = null;
  els.opLabel.textContent = entry.label;
  els.computeBtn.disabled = false;
  setStatus('done');
  closeHistoryDrawer();
}

/* ─────────────────────────────────────────────────────────────────────────
   Blur autosave
   ───────────────────────────────────────────────────────────────────────── */

/** On textarea blur: silently parse and pre-populate the grid. */
function wireAutosave(textEl, gridId, rowKey, colKey, rowInput, colInput) {
  textEl.addEventListener('blur', async () => {
    const text = textEl.value.trim();
    if (!text) return;
    const data = await fetchParse(text);
    if (data) {
      populateGrid(gridId, data, rowKey, colKey, rowInput, colInput);
    }
  });
}

/* ─────────────────────────────────────────────────────────────────────────
   Initialisation
   ───────────────────────────────────────────────────────────────────────── */

let opBtns;

function init() {
  // 1. Op-group accordion + localStorage
  document.querySelectorAll('.op-group').forEach(g => {
    g.style.setProperty('--group-color', g.dataset.color);
    const header = g.querySelector('.group-header');
    const body   = g.querySelector('.group-body');
    if (!header || !body) return;
    const labelText  = g.querySelector('.group-label')?.textContent.trim() || '';
    const storageKey = labelText ? `la-studio-op-group-${labelText}` : null;
    if (storageKey && localStorage.getItem(storageKey) === 'collapsed') {
      g.classList.add('collapsed');
      header.setAttribute('aria-expanded', 'false');
    } else {
      header.setAttribute('aria-expanded', 'true');
    }
    header.addEventListener('click', () => {
      const nowCollapsed = g.classList.toggle('collapsed');
      header.setAttribute('aria-expanded', nowCollapsed ? 'false' : 'true');
      if (storageKey) localStorage.setItem(storageKey, nowCollapsed ? 'collapsed' : 'open');
    });
    header.addEventListener('keydown', e => {
      if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); header.click(); }
    });
  });

  // 2. Build Matrix A grid
  initGridA();

  // 3. Matrix A dim controls
  els.updateA.addEventListener('click', applyDimA);
  els.rowsA.addEventListener('keydown', e => e.key === 'Enter' && applyDimA());
  els.colsA.addEventListener('keydown', e => e.key === 'Enter' && applyDimA());
  els.clearA.addEventListener('click', () => clearGrid('gridA'));

  // 4. Text mode toggles
  els.toggleModeA.addEventListener('click', toggleTextModeA);
  els.toggleModeB.addEventListener('click', toggleTextModeB);
  els.toggleModeC.addEventListener('click', toggleTextModeC);

  // 5. Autosave on textarea blur
  wireAutosave(els.textA, 'gridA', 'rowsA', 'colsA', els.rowsA, els.colsA);
  wireAutosave(els.textB, 'gridB', 'rowsB', 'colsB', els.rowsB, els.colsB);
  wireAutosave(els.textC, 'gridC', 'rowsC', 'colsC', els.rowsC, els.colsC);

  // 6. Matrix B dim controls
  els.updateB.addEventListener('click', applyDimB);
  els.rowsB.addEventListener('keydown', e => e.key === 'Enter' && applyDimB());
  els.colsB.addEventListener('keydown', e => e.key === 'Enter' && applyDimB());

  // 7. Chain multiply segment controls
  [els.modSegA, els.modSegB, els.modSegC].forEach(seg => {
    if (!seg) return;
    seg.querySelectorAll('.mod-seg-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        seg.querySelectorAll('.mod-seg-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      });
    });
  });

  // 8. Chain multiply: M3 toggle
  els.addM3Btn.addEventListener('click', () => {
    state.chain.showM3 = !state.chain.showM3;
    if (state.chain.showM3) {
      createGrid('gridC', state.rowsC, state.colsC);
      els.cardC.classList.remove('hidden');
      els.addM3Btn.classList.add('m3-active');
      els.addM3Btn.innerHTML = '<svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true"><path d="M2 2l8 8M10 2l-8 8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg> Remove third matrix';
    } else {
      els.cardC.classList.add('hidden');
      els.addM3Btn.classList.remove('m3-active');
      els.addM3Btn.innerHTML = '<svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true"><path d="M6 1v10M1 6h10" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg> Add third matrix';
      if (els.modSegC) {
        els.modSegC.querySelectorAll('.mod-seg-btn').forEach(b => b.classList.remove('active'));
        const noneBtn = els.modSegC.querySelector('[data-mod="none"]');
        if (noneBtn) noneBtn.classList.add('active');
      }
    }
  });

  // 9. Matrix C dim controls
  els.updateC.addEventListener('click', async () => {
    const r = parseInt(els.rowsC.value, 10);
    const c = parseInt(els.colsC.value, 10);
    if (!r || !c || r < 1 || c < 1) return;

    pushUndo();

    if (state.textModeC) {
      const text = els.textC.value.trim();
      if (text) {
        const data = await fetchParse(text);
        if (data) populateGrid('gridC', data, 'rowsC', 'colsC', els.rowsC, els.colsC);
      }
      state.textModeC = false;
      els.textWrapC.classList.add('hidden');
      els.gridC.classList.remove('hidden');
    }

    const saved = saveGrid('gridC');
    state.rowsC = r;
    state.colsC = c;
    createGrid('gridC', r, c);
    restoreGrid('gridC', saved);
  });
  els.rowsC.addEventListener('keydown', e => e.key === 'Enter' && els.updateC.click());
  els.colsC.addEventListener('keydown', e => e.key === 'Enter' && els.updateC.click());

  // 10. Operation buttons — select only, Compute button runs
  opBtns = document.querySelectorAll('.op-btn');
  opBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const op = btn.dataset.op;
      if (!op) return;
      selectOp(op, btn.dataset.needs);
    });
  });

  // 11. Compute button
  els.computeBtn.addEventListener('click', runOperation);

  // 12. Keyboard shortcut: Cmd/Ctrl+Enter to compute; Cmd/Ctrl+Z/Y for undo/redo
  document.addEventListener('keydown', e => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      if (state.activeOp && !els.computeBtn.disabled) runOperation();
    }
    if ((e.metaKey || e.ctrlKey) && e.key === 'z' && !e.shiftKey) {
      e.preventDefault();
      performUndo();
    }
    if ((e.metaKey || e.ctrlKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
      e.preventDefault();
      performRedo();
    }
  });

  // 13. Steps collapse toggle
  els.toggleSteps.addEventListener('click', () => {
    state.stepsCollapsed = !state.stepsCollapsed;
    applyStepsVisibility();
  });

  // 14. Help modal
  els.helpBtn.addEventListener('click', openHelpModal);
  els.closeHelpModal.addEventListener('click', closeHelpModal);
  els.helpModal.addEventListener('click', e => { if (e.target === els.helpModal) closeHelpModal(); });

  // 14b. Equivalent statements
  els.equivBtn.addEventListener('click', openEquivModal);
  els.closeModal.addEventListener('click', closeEquivModal);
  els.equivModal.addEventListener('click', e => { if (e.target === els.equivModal) closeEquivModal(); });

  // 15. Cancel button
  els.cancelBtn.addEventListener('click', () => {
    if (state.currentAbort) { state.currentAbort.abort(); state.currentAbort = null; }
  });

  // 16. Copy button
  els.copyBtn.addEventListener('click', () => {
    if (!state.lastRaw) return;
    navigator.clipboard.writeText(state.lastRaw).then(() => {
      els.copyBtn.textContent = '✓ Copied';
      setTimeout(() => { els.copyBtn.textContent = 'Copy'; }, 500);
    }).catch(() => {
      els.copyBtn.textContent = 'Failed';
      setTimeout(() => { els.copyBtn.textContent = 'Copy'; }, 1000);
    });
  });

  // 17. History drawer
  els.historyBtn.addEventListener('click', openHistoryDrawer);
  els.closeHistoryBtn.addEventListener('click', closeHistoryDrawer);
  els.historyBackdrop.addEventListener('click', closeHistoryDrawer);
  els.clearHistoryBtn.addEventListener('click', () => {
    _history.length = 0;
    updateHistoryCount();
    renderHistoryList();
  });

  // 18. Keyboard: Escape + Tab trap
  document.addEventListener('keydown', e => {
    if (!els.settingsPopover.classList.contains('hidden')) {
      if (e.key === 'Escape') { closeSettings(); return; }
    }
    if (!els.historyBackdrop.classList.contains('hidden')) {
      if (e.key === 'Escape') { closeHistoryDrawer(); return; }
    }
    if (!els.helpModal.classList.contains('hidden')) {
      if (e.key === 'Escape') { closeHelpModal(); return; }
    }
    if (els.equivModal.classList.contains('hidden')) return;
    if (e.key === 'Escape') {
      closeEquivModal();
    } else if (e.key === 'Tab') {
      if (!_modalFocusable.length) { e.preventDefault(); return; }
      const first = _modalFocusable[0];
      const last  = _modalFocusable[_modalFocusable.length - 1];
      if (e.shiftKey) {
        if (document.activeElement === first) { e.preventDefault(); last.focus(); }
      } else {
        if (document.activeElement === last)  { e.preventDefault(); first.focus(); }
      }
    }
  });

  // 19. Settings popover
  els.settingsBtn.addEventListener('click', e => {
    e.stopPropagation();
    if (els.settingsPopover.classList.contains('hidden')) openSettings();
    else closeSettings();
  });
  els.settingsClose.addEventListener('click', closeSettings);
  document.addEventListener('click', e => {
    if (!els.settingsPopover.classList.contains('hidden') &&
        !els.settingsPopover.contains(e.target) &&
        e.target !== els.settingsBtn) {
      closeSettings();
    }
  });
  els.darkToggle.addEventListener('click', () => {
    applyDarkMode(els.darkToggle.getAttribute('aria-checked') !== 'true');
  });
  els.autoLinkToggle.addEventListener('click', () => {
    applyAutoLinkPref(els.autoLinkToggle.getAttribute('aria-checked') !== 'true');
  });

  // 20. Load saved settings
  applyDarkMode(localStorage.getItem('la-studio-dark') === '1');
  applyAutoLinkPref(localStorage.getItem('la-studio-autolink') !== '0');

  // 21. Undo/redo buttons
  els.undoBtn.addEventListener('click', performUndo);
  els.redoBtn.addEventListener('click', performRedo);
  updateUndoButtons();
}

document.addEventListener('DOMContentLoaded', init);
