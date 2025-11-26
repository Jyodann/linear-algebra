document.addEventListener('DOMContentLoaded', () => {
    const matrixInput = document.getElementById('matrixInput');
    const resultDisplay = document.getElementById('resultDisplay');
    const statusLabel = document.getElementById('status');
    const buttons = document.querySelectorAll('.op-btn');

    // Grid Elements
    const matrixGrid = document.getElementById('matrixGrid');
    const rowsInput = document.getElementById('rows');
    const colsInput = document.getElementById('cols');
    const updateGridBtn = document.getElementById('updateGridBtn');
    const clearGridBtn = document.getElementById('clearGridBtn');
    const toggleInputModeBtn = document.getElementById('toggleInputMode');
    const textInputArea = document.getElementById('textInputArea');
    const matrixGridContainer = document.querySelector('.matrix-grid'); // wrapper for grid
    const matrixControls = document.querySelector('.matrix-controls');

    let isGridMode = true;

    // Initialize Grid
    createGrid(2, 2);

    updateGridBtn.addEventListener('click', () => {
        const r = parseInt(rowsInput.value);
        const c = parseInt(colsInput.value);
        if (r > 0 && c > 0 && r <= 10 && c <= 10) {
            createGrid(r, c);
        } else {
            showError("Dimensions must be between 1 and 10");
        }
    });

    clearGridBtn.addEventListener('click', () => {
        const inputs = matrixGrid.querySelectorAll('input');
        inputs.forEach(input => input.value = '');
    });

    toggleInputModeBtn.addEventListener('click', () => {
        isGridMode = !isGridMode;
        if (isGridMode) {
            matrixGrid.classList.remove('hidden');
            matrixControls.classList.remove('hidden');
            textInputArea.classList.add('hidden');
            toggleInputModeBtn.textContent = 'Switch to Text/LaTeX Input';
        } else {
            matrixGrid.classList.add('hidden');
            matrixControls.classList.add('hidden');
            textInputArea.classList.remove('hidden');
            toggleInputModeBtn.textContent = 'Switch to Grid Input';
        }
    });

    function createGrid(rows, cols) {
        matrixGrid.style.gridTemplateColumns = `repeat(${cols}, auto)`;
        matrixGrid.innerHTML = '';

        for (let i = 0; i < rows; i++) {
            for (let j = 0; j < cols; j++) {
                const input = document.createElement('input');
                input.type = 'text';
                input.className = 'grid-cell';
                input.placeholder = '0';
                input.dataset.row = i;
                input.dataset.col = j;

                // Dynamic Resizing
                input.addEventListener('input', () => {
                    const len = input.value.length;
                    // Base width is 80px (approx 8ch). Expand if longer.
                    // Using ch unit for monospace font is reliable.
                    if (len > 6) {
                        input.style.width = `${len + 3}ch`;
                    } else {
                        input.style.width = ''; // Revert to CSS default
                    }
                });

                matrixGrid.appendChild(input);
            }
        }
    }

    function getMatrixFromGrid() {
        const rows = parseInt(rowsInput.value);
        const cols = parseInt(colsInput.value);
        const matrix = [];

        const inputs = matrixGrid.querySelectorAll('input');
        let currentIndex = 0;

        for (let i = 0; i < rows; i++) {
            const row = [];
            for (let j = 0; j < cols; j++) {
                const val = inputs[currentIndex].value.trim();
                row.push(val === '' ? '0' : val);
                currentIndex++;
            }
            matrix.push(row);
        }
        return JSON.stringify(matrix);
    }

    // Equivalent Statements Elements
    const equivBtn = document.getElementById('equivBtn');
    const equivModal = document.getElementById('equivModal');
    const closeModal = document.querySelector('.close-modal');
    const equivCategory = document.getElementById('equivCategory');
    const equivProperties = document.getElementById('equivProperties');
    const equivList = document.getElementById('equivList');

    equivBtn.addEventListener('click', async () => {
        let matrixStr = "";
        if (isGridMode) {
            matrixStr = getMatrixFromGrid();
        } else {
            matrixStr = matrixInput.value.trim();
        }

        if (!matrixStr) {
            showError('Please enter a matrix first.');
            return;
        }

        setLoading(true);

        try {
            const response = await fetch('/api/equivalent', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    matrix: matrixStr
                })
            });

            const data = await response.json();

            if (response.ok) {
                showEquivalentStatements(data);
            } else {
                showError(data.error || 'An error occurred');
            }
        } catch (error) {
            showError('Network error: ' + error.message);
        } finally {
            setLoading(false);
        }
    });

    function showEquivalentStatements(data) {
        equivCategory.textContent = data.category;

        // Clear previous
        equivProperties.innerHTML = '';
        equivList.innerHTML = '';

        // Add properties tags
        const props = data.properties;
        const tags = [
            `${props.rows} × ${props.cols}`,
            `Rank: ${props.rank}`,
            `Nullity: ${props.nullity}`
        ];

        tags.forEach(tag => {
            const span = document.createElement('span');
            span.className = 'prop-tag';
            span.textContent = tag;
            equivProperties.appendChild(span);
        });

        // Add statements
        data.statements.forEach(stmt => {
            const li = document.createElement('li');
            li.innerHTML = stmt.replace(/R\^n/g, 'ℝⁿ').replace(/R\^m/g, 'ℝᵐ'); // Simple formatting
            equivList.appendChild(li);
        });

        equivModal.classList.remove('hidden');
    }

    closeModal.addEventListener('click', () => {
        equivModal.classList.add('hidden');
    });

    window.addEventListener('click', (event) => {
        if (event.target == equivModal) {
            equivModal.classList.add('hidden');
        }
    });

    buttons.forEach(btn => {
        btn.addEventListener('click', async () => {
            const operation = btn.dataset.op;
            let matrixStr = "";

            if (isGridMode) {
                matrixStr = getMatrixFromGrid();
            } else {
                matrixStr = matrixInput.value.trim();
            }

            if (!matrixStr) {
                showError('Please enter a matrix first.');
                return;
            }

            setLoading(true);

            try {
                const response = await fetch('/api/process', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        matrix: matrixStr,
                        operation: operation
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    showResult(data.result);
                } else {
                    showError(data.error || 'An error occurred');
                }
            } catch (error) {
                showError('Network error: ' + error.message);
            } finally {
                setLoading(false);
            }
        });
    });

    function setLoading(isLoading) {
        if (isLoading) {
            statusLabel.textContent = 'Processing...';
            statusLabel.className = 'status loading';
            resultDisplay.style.opacity = '0.5';
        } else {
            statusLabel.textContent = 'Ready';
            statusLabel.className = 'status';
            resultDisplay.style.opacity = '1';
        }
    }

    function showResult(latex) {
        resultDisplay.innerHTML = latex;
        // Trigger MathJax typeset
        if (window.MathJax) {
            MathJax.typesetPromise([resultDisplay]).catch((err) => console.log(err));
        }
    }

    function showError(message) {
        statusLabel.textContent = 'Error';
        statusLabel.className = 'status error';
        resultDisplay.innerHTML = `<div style="color: var(--error); text-align: center;">${message}</div>`;
    }
});
