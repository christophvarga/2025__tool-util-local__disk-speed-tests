/**
 * QLab Disk Performance Tester - Disk & Test Management Module
 * Disk loading/selection, test types, custom tests, test control.
 */

DiskBenchApp.prototype.loadAvailableDisks = async function() {
    const diskList = document.getElementById('diskList');
    diskList.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Loading available disks...</div>';

    try {
        const result = await this.executeDiskBenchCommand(['--list-disks', '--json']);
        if (result && result.disks) {
            this.availableDisks = result.disks;
            this.renderDiskList(result.disks);
        } else {
            throw new Error('No disk data received');
        }
    } catch (error) {
        console.error('Failed to load disks:', error);
        diskList.innerHTML = `
            <div class="loading">
                <i class="fas fa-exclamation-triangle"></i>
                Failed to load disks. Please ensure the diskbench helper binary is available.
                <br><br>
                <button class="btn btn-secondary" onclick="app.loadAvailableDisks()">
                    <i class="fas fa-retry"></i> Retry
                </button>
            </div>
        `;
    }
};

DiskBenchApp.prototype.renderDiskList = function(disks) {
    const diskList = document.getElementById('diskList');
    const template = document.getElementById('disk-item-template');

    if (!disks || disks.length === 0) {
        diskList.innerHTML = '<div class="loading"><i class="fas fa-info-circle"></i> No suitable disks found for testing.</div>';
        return;
    }

    diskList.innerHTML = '';
    disks.filter(disk => disk.suitable_for_testing).forEach(disk => {
        const clone = template.content.cloneNode(true);
        const diskItem = clone.querySelector('.disk-item');
        diskItem.dataset.diskPath = disk.device;

        const isSelected = this.selectedDisk && this.selectedDisk.device === disk.device;
        if (isSelected) {
            diskItem.classList.add('selected');
            clone.querySelector('input[type="radio"]').checked = true;
        }
        clone.querySelector('input[type="radio"]').value = disk.device;

        const alias = this.getDiskAlias(disk.device);
        const nameEl = clone.querySelector('.disk-name');
        if (alias) {
            nameEl.innerHTML = `${this._escapeHTML(alias)} <span class="disk-original-name">(${this._escapeHTML(disk.name)})</span>`;
        } else {
            nameEl.textContent = disk.name;
        }

        const detailsText = `${disk.device} • ${disk.size} • ${disk.file_system}${disk.free_space ? ` • ${disk.free_space} free` : ''}`;
        clone.querySelector('.disk-details').textContent = detailsText;

        const typeEl = clone.querySelector('.disk-meta');
        typeEl.textContent = disk.type;
        typeEl.className = `disk-type ${disk.type ? disk.type.toLowerCase() : ''}`;

        diskItem.addEventListener('click', () => this.selectDisk(disk.device, disk));
        diskList.appendChild(clone);
    });
};

DiskBenchApp.prototype.selectDisk = function(diskPath, diskInfo) {
    this.selectedDisk = diskInfo;
    document.querySelectorAll('.disk-item').forEach(item => {
        item.classList.remove('selected');
        item.querySelector('input[type="radio"]').checked = false;
    });

    const selectedItem = document.querySelector(`[data-disk-path="${diskPath}"]`);
    if (selectedItem) {
        selectedItem.classList.add('selected');
        selectedItem.querySelector('input[type="radio"]').checked = true;
    }

    const aliasInput = document.getElementById('diskAliasInput');
    const saveAliasBtn = document.getElementById('saveDiskAlias');
    if (aliasInput) { aliasInput.disabled = false; aliasInput.value = this.getDiskAlias(diskPath) || ''; }
    if (saveAliasBtn) saveAliasBtn.disabled = false;
    this.updateUI();
};

DiskBenchApp.prototype.loadTests = async function() {
    try {
        const resp = await fetch('/api/tests');
        const data = await resp.json();
        if (!data || !data.success || !data.tests || !data.order) {
            console.warn('Tests API returned unexpected format', data);
            return;
        }
        this.renderTestOptions(data.tests, data.order);
        if (!this.selectedTestType && data.order.length > 0) {
            this.selectedTestType = data.order[0];
            const firstRadio = document.querySelector(`input[name="testType"][value="${this.selectedTestType}"]`);
            if (firstRadio) firstRadio.checked = true;
        }
        this.updateUI();
        this.updateTestDescription();
    } catch (e) {
        console.error('Failed to load tests:', e);
    }
};

DiskBenchApp.prototype.renderTestOptions = function(testsById, order) {
    const container = document.querySelector('.test-types');
    const template = document.getElementById('test-option-template');
    if (!container || !template) return;

    this.testsCatalog = { tests: testsById, order };
    container.innerHTML = '';

    order.forEach(id => {
        const t = testsById[id] || {};
        const clone = template.content.cloneNode(true);
        const radio = clone.querySelector('input[type="radio"]');
        radio.value = id;
        if (this.selectedTestType === id) radio.checked = true;

        const label = t.display_label || id;
        clone.querySelector('.test-label').textContent = `${label}: ${t.name || id}`;

        if (label === 'Test 1') {
            clone.querySelector('.test-card').classList.add('recommended');
            clone.querySelector('.badge').classList.remove('hidden');
        }

        clone.querySelector('.info-icon').onclick = (e) => { e.preventDefault(); showPatternInfo(id); };
        clone.querySelector('.test-description').textContent = t.description || '';

        const minutes = t.duration ? Math.round(t.duration / 60) : null;
        if (minutes) clone.querySelector('.test-duration').textContent = `⏱️ Dauer: ${minutes} Minuten`;
        container.appendChild(clone);
    });

    // Custom tests
    if (this.customTests) {
        Object.entries(this.customTests).forEach(([id, test]) => {
            const clone = template.content.cloneNode(true);
            const radio = clone.querySelector('input[type="radio"]');
            radio.value = id;
            if (this.selectedTestType === id) radio.checked = true;
            clone.querySelector('.test-label').textContent = test.name;
            clone.querySelector('.test-description').textContent =
                `${test.params.block_size} blocks, ${test.params.rw_mix}% Read, ${test.params.numjobs} jobs`;
            const minutes = Math.round(test.params.duration / 60);
            clone.querySelector('.test-duration').textContent = `⏱️ Duration: ${minutes < 1 ? test.params.duration + 's' : minutes + 'm'}`;

            const card = clone.querySelector('.test-card');
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'btn-delete-custom';
            deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
            deleteBtn.onclick = (e) => { e.preventDefault(); e.stopPropagation(); if (confirm(`Delete custom test "${test.name}"?`)) this.deleteCustomTest(id); };
            card.appendChild(deleteBtn);
            clone.querySelector('.info-icon').style.display = 'none';
            container.appendChild(clone);
        });
    }

    // Create Custom Test button
    const createBtn = document.createElement('div');
    createBtn.className = 'test-option';
    createBtn.id = 'createCustomTestBtn';
    createBtn.innerHTML = `<div class="test-card create-custom"><div class="create-icon"><i class="fas fa-plus-circle"></i></div><h4>Create Custom Test</h4><p>Define your own parameters</p></div>`;
    createBtn.addEventListener('click', () => this.openCustomTestModal());
    container.appendChild(createBtn);

    this.bindTestTypeListeners();
    this.updateTestDescription();
};

DiskBenchApp.prototype.loadCustomTests = function() {
    try {
        const stored = localStorage.getItem('qlab_custom_tests');
        this.customTests = stored ? JSON.parse(stored) : {};
    } catch (e) {
        console.error('Failed to load custom tests', e);
        this.customTests = {};
    }
};

DiskBenchApp.prototype.saveCustomTest = function() {
    const name = document.getElementById('customTestName').value.trim();
    if (!name) { alert('Please enter a test name'); return; }

    const params = {
        name, block_size: document.getElementById('customBlockSize').value.trim(),
        duration: parseInt(document.getElementById('customDuration').value),
        rw_mix: parseInt(document.getElementById('customRwMix').value),
        numjobs: parseInt(document.getElementById('customNumJobs').value),
        iodepth: parseInt(document.getElementById('customIoDepth').value),
        target_rate: document.getElementById('customTargetRate').value.trim()
    };

    const id = 'custom_' + Date.now();
    this.customTests[id] = { id, name, params };
    localStorage.setItem('qlab_custom_tests', JSON.stringify(this.customTests));
    this.closeCustomTestModal();
    this.loadTests();
};

DiskBenchApp.prototype.deleteCustomTest = function(id) {
    if (this.customTests[id]) {
        delete this.customTests[id];
        localStorage.setItem('qlab_custom_tests', JSON.stringify(this.customTests));
        if (this.selectedTestType === id) this.selectedTestType = null;
        this.loadTests();
    }
};

DiskBenchApp.prototype.openCustomTestModal = function() {
    document.getElementById('customTestModal').classList.remove('hidden');
};

DiskBenchApp.prototype.closeCustomTestModal = function() {
    document.getElementById('customTestModal').classList.add('hidden');
    document.getElementById('customTestForm').reset();
    document.getElementById('rwMixValue').textContent = '50';
};

DiskBenchApp.prototype.updateTestDescription = function() {
    const descEl = document.getElementById('testDescription');
    if (!descEl) return;

    let selected = this.selectedTestType;
    if (!selected) {
        const checked = document.querySelector('input[name="testType"]:checked');
        if (checked) selected = checked.value;
    }

    if (!selected) {
        descEl.innerHTML = `<div class="loading"><i class="fas fa-info-circle"></i> Select a test to see details.</div>`;
        return;
    }

    const catalog = (this.testsCatalog && this.testsCatalog.tests) ? this.testsCatalog.tests : null;
    const staticMap = {
        'quick_max_speed': { name: 'Quick Max Speed Test', description: 'Schneller Maximaltest (ca. 1 Minute). Eignet sich für eine schnelle Einschätzung der maximalen Lese-/Schreibgeschwindigkeit.', duration: 60 },
        'qlab_prores_422_show': { name: 'QLab ProRes 422 Show Pattern', description: 'Realistische QLab-Show (2,75h): 1x4K + 3xHD ProRes 422 inkl. Crossfades. Bewertet Stabilität und Durchsatz.', duration: 9900 },
        'qlab_prores_hq_show': { name: 'QLab ProRes HQ Show Pattern', description: 'Anspruchsvolle QLab-Show (2,75h) mit ProRes HQ. Eignet sich für 4K/HQ-Workflows und Worst-Case Crossfades.', duration: 9900 },
        'thermal_maximum_analyser': { name: 'Thermal Maximum Analyser', description: '1,5h Dauerlast zur Erkennung von thermischem Throttling und Langzeitverhalten.', duration: 5400 }
    };

    const t = (catalog && catalog[selected]) ? catalog[selected] : staticMap[selected] || {};
    const title = t.display_label ? `${t.display_label}: ${t.name || ''}` : (t.name || selected);
    const desc = t.description || '';
    const minutes = t.duration ? Math.round(t.duration / 60) : null;

    descEl.innerHTML = `
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;color:var(--dark-color)">
            <i class="fas fa-circle-info" style="color:var(--info-color)"></i>
            <strong>${this._escapeHTML(title)}</strong>
        </div>
        <p>${this._escapeHTML(desc)}</p>
        ${minutes ? `<div class="test-duration">⏱️ Duration: ${this._escapeHTML(minutes)} minutes</div>` : ''}
    `;
};

// Test control methods (startTest, stopTest, etc.) are in app-api.js
