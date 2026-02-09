/**
 * QLab Disk Performance Tester - Test Control Module
 * Start, stop, and manage test execution.
 */

DiskBenchApp.prototype.startTest = async function() {
    if (!this.selectedDisk || this.isTestRunning) return;

    this.isTestRunning = true;
    this.testResults = null;
    this.currentTestDuration = 0;

    document.getElementById('progressSection').classList.remove('hidden');
    document.getElementById('resultsSection').classList.add('hidden');
    document.getElementById('startTest').classList.add('hidden');
    document.getElementById('stopTest').classList.remove('hidden');
    document.getElementById('stopAllTests').classList.add('hidden');
    document.getElementById('exportResults').classList.add('hidden');
    this.updateProgress(0, 'Preparing test...');

    if (this.bandwidthChart) {
        this.bandwidthChart.data.labels = [];
        this.bandwidthChart.data.datasets.forEach(ds => { ds.data = []; });
        this.bandwidthChart.update();
    }

    ['copyResults', 'copyCli', 'downloadSummary'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.add('hidden');
    });

    try {
        const payload = { disk_path: this.selectedDisk.device, size_gb: this.testSize, show_progress: true };

        if (this.selectedTestType.startsWith('custom_')) {
            const customTest = this.customTests[this.selectedTestType];
            if (!customTest) throw new Error('Custom test definition not found');
            payload.test_type = 'custom';
            payload.custom_params = customTest.params;
            this.updateProgressDetails(`Starting Custom Test: ${customTest.name}`);
        } else {
            payload.test_type = this.selectedTestType;
            this.updateProgressDetails(`Command: diskbench --test ${this.selectedTestType} ...`);
        }

        this.lastRunParams = {
            test_type: this.selectedTestType, disk_path: this.selectedDisk.device,
            disk_alias: this.getDiskAlias(this.selectedDisk.device) || '',
            size_gb: this.testSize, saved_at: new Date().toISOString()
        };
        this.saveLastRun();
        this.updateProgress(5, 'Starting FIO test...');

        const result = await this.callBridgeAPI('/api/test/start', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (result && result.success) {
            this.currentTestId = result.test_id;
            this.updateProgress(5, 'Test started successfully...');
            this.updateProgressDetails('Test is now running in background. Polling for updates...');
        } else {
            throw new Error(result.error || 'Failed to start test');
        }
    } catch (error) {
        console.error('Test failed:', error);
        this.updateProgress(0, `Test failed: ${error.message}`);
        this.updateProgressDetails(`Error: ${error.message}`);
        this.isTestRunning = false;
        this.currentTestId = null;
        this.updateUI();
        document.getElementById('startTest').classList.remove('hidden');
        document.getElementById('stopTest').classList.add('hidden');
        document.getElementById('stopAllTests').classList.add('hidden');
    }
};

DiskBenchApp.prototype.stopTest = async function() {
    if (!this.isTestRunning || !this.currentTestId) return;
    try {
        const result = await this.callBridgeAPI(`/api/test/stop/${this.currentTestId}`, { method: 'POST' });
        if (result.success) this.handleTestStopped('Test stopped by user');
        else throw new Error(result.error || 'Failed to stop test');
    } catch (error) {
        console.error('Stop test failed:', error);
        this.handleTestStopped(`Stop failed: ${error.message}`);
    }
};

DiskBenchApp.prototype.stopAllTests = async function() {
    if (!this.isTestRunning) return;
    try {
        const result = await this.callBridgeAPI('/api/test/stop-all', { method: 'POST' });
        if (result.success) this.handleTestStopped('All tests stopped by user');
        else throw new Error(result.error || 'Failed to stop all tests');
    } catch (error) {
        console.error('Stop all tests failed:', error);
        this.handleTestStopped(`Stop all failed: ${error.message}`);
    }
};

DiskBenchApp.prototype.handleTestStopped = function(message) {
    this.isTestRunning = false;
    this.currentTestId = null;
    this.resetCircuitBreaker();
    this.hideConnectionWarning();
    this.updateProgress(0, message);
    this.updateUI();
    document.getElementById('startTest').classList.remove('hidden');
    document.getElementById('stopTest').classList.add('hidden');
    document.getElementById('stopAllTests').classList.add('hidden');
};

DiskBenchApp.prototype.checkForActiveTest = function() {
    this.callBridgeAPI('/api/test/current')
        .then(result => {
            if (result.success && result.test_running) {
                this.isTestRunning = true;
                this.currentTestId = result.test_info.test_id;
                this.currentTestDuration = result.test_info.estimated_duration || 0;
                this.showBackgroundTestNotice(result.test_info);

                if (
                    result.test_info.status === 'disconnected' ||
                    result.test_info.status === 'unknown'
                ) {
                    this.showDisconnectedCleanupUI(result.test_info);
                    this.updateUI();
                    return;
                }

                this.updateUI();
                this.pollTestStatus(this.currentTestId);
            } else {
                this.hideBackgroundTestNotice();
            }
        })
        .catch(error => {
            console.error('Error checking for active test:', error);
            this.hideBackgroundTestNotice();
        });
};

DiskBenchApp.prototype.showBackgroundTestNotice = function(testInfo) {
    let notice = document.getElementById('backgroundTestNotice');
    if (!notice) {
        notice = document.createElement('div');
        notice.id = 'backgroundTestNotice';
        notice.className = 'background-notice';
        document.body.appendChild(notice);
    }

    const testType = testInfo.test_type || this.selectedTestType || 'unknown';
    const progress = typeof testInfo.progress === 'number' ? testInfo.progress : 0;
    const elapsedTime = testInfo.elapsed_time || 0;
    const remainingTime = testInfo.remaining_time || 0;

    const _e = (s) => this._escapeHTML(s);
    notice.innerHTML = `
        <div class="notice-content">
            <div class="notice-header">
                <i class="fas fa-spinner fa-spin"></i>
                <strong>Test in Progress</strong>
            </div>
            <div class="notice-details">
                <div class="test-info">
                    <span class="test-name">${_e(this.getTestDisplayName(testType))}</span>
                    <span class="test-progress">${_e(progress.toFixed(1))}% complete</span>
                </div>
                <div class="timing-info">
                    <span class="elapsed">Elapsed: ${_e(this.formatDuration(elapsedTime))}</span>
                    <span class="remaining">Remaining: ${_e(this.formatDuration(remainingTime))}</span>
                </div>
            </div>
            <div class="notice-actions">
                <button id="stopBackgroundTest" class="btn btn-danger btn-sm">
                    <i class="fas fa-stop"></i> Stop Test
                </button>
            </div>
        </div>
    `;

    const stopButton = document.getElementById('stopBackgroundTest');
    if (stopButton) {
        stopButton.replaceWith(stopButton.cloneNode(true));
        const newStopButton = document.getElementById('stopBackgroundTest');
        newStopButton.addEventListener('click', this.stopTest.bind(this));
    }

    notice.classList.remove('hidden');
};

DiskBenchApp.prototype.hideBackgroundTestNotice = function() {
    const notice = document.getElementById('backgroundTestNotice');
    if (notice) notice.classList.add('hidden');
};

DiskBenchApp.prototype.checkFio = async function() {
    try {
        const res = await this.callBridgeAPI('/api/fio-info');
        if (!res.success) {
            this.showFioWarning(res.error || 'fio not installed');
        }
    } catch (err) {
        this.showFioWarning('Cannot contact bridge server or /api/fio-info');
    }
};

DiskBenchApp.prototype.showFioWarning = function(message) {
    let banner = document.getElementById('fioWarning');
    if (!banner) {
        banner = document.createElement('div');
        banner.id = 'fioWarning';
        banner.style.background = '#ffdddd';
        banner.style.border = '1px solid #d33';
        banner.style.padding = '10px';
        banner.style.marginBottom = '10px';
        banner.style.fontWeight = 'bold';
        banner.style.fontFamily = 'system-ui, sans-serif';
        document.body.prepend(banner);
    }
    banner.textContent = '';
    const warningText = document.createTextNode(`\u26A0\uFE0F  ${message}. Install FIO with `);
    const code = document.createElement('code');
    code.textContent = 'brew install fio';
    const suffix = document.createTextNode(' and reload.');
    banner.appendChild(warningText);
    banner.appendChild(code);
    banner.appendChild(suffix);
};
