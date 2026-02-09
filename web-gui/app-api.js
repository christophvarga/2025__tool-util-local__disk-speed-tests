/**
 * QLab Disk Performance Tester - API & Polling Module
 * Bridge API calls, polling, circuit breaker, connection management.
 */

DiskBenchApp.prototype.callBridgeAPI = async function(endpoint, options = {}) {
    const url = DiskBenchApp.BRIDGE_URL + endpoint;
    const timeoutMs = options.timeout || DiskBenchApp.API_TIMEOUT_MS;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    const defaultOptions = {
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        signal: controller.signal
    };

    const mergedOptions = { ...defaultOptions, ...options };
    delete mergedOptions.timeout;

    if (mergedOptions.body && !mergedOptions.method) {
        mergedOptions.method = 'POST';
    }

    try {
        const response = await fetch(url, mergedOptions);
        if (!response.ok) {
            let errorMsg = `HTTP error! status: ${response.status}`;
            try { const d = await response.json(); errorMsg = d.error || errorMsg; } catch (e) {}
            throw new Error(errorMsg);
        }
        return await response.json();
    } catch (error) {
        if (error.name === 'AbortError') {
            throw new Error(`Request to ${endpoint} timed out after ${timeoutMs}ms`);
        }
        console.error(`API call failed for ${url}:`, error);
        throw error;
    } finally {
        clearTimeout(timeoutId);
    }
};

DiskBenchApp.prototype.executeDiskBenchCommand = async function(args) {
    if (args[0] === '--list-disks' && args[1] === '--json') {
        return await this.callBridgeAPI('/api/disks');
    }

    if (args[0] === '--test') {
        const testType = args[1];
        const diskPath = args[3];
        const size = parseInt(args[5]);
        const outputFile = args[7];
        const showProgress = args.includes('--progress');

        const testParams = {
            test_type: testType, disk_path: diskPath,
            size_gb: size, output_file: outputFile, show_progress: showProgress
        };

        const startResult = await this.callBridgeAPI('/api/test/start', {
            method: 'POST', body: JSON.stringify(testParams)
        });

        if (startResult.success) {
            this.currentTestId = startResult.test_id;
            this.currentTestDuration = startResult.estimated_duration || 0;
            this.pollTestStatus(this.currentTestId);
            return {
                success: true,
                test_info: {
                    test_id: this.currentTestId, status: 'started',
                    disk_path: diskPath, test_type: testType,
                    estimated_duration: this.currentTestDuration
                }
            };
        } else {
            throw new Error(startResult.error || 'Failed to start test');
        }
    }

    if (args[0] === '--version') return await this.callBridgeAPI('/api/version');
    if (args[0] === '--validate') return await this.callBridgeAPI('/api/validate');
    throw new Error(`Unsupported command: ${args[0]}`);
};

DiskBenchApp.prototype.pollTestStatus = async function(testId) {
    if (!testId) return;

    const cb = this.circuitBreaker;
    if (cb.state === 'open') {
        console.warn('Circuit breaker OPEN: polling suspended.');
        this.showConnectionWarning();
        return;
    }

    try {
        const result = await this.callBridgeAPI(`/api/test/${testId}`);
        this.resetCircuitBreaker();
        this.hideConnectionWarning();

        if (result.success && result.test_info) {
            const testInfo = result.test_info;
            this.updateEnhancedProgress(testInfo);
            this.updateProgressDetails(`Phase: ${testInfo.current_phase || 'Running'} | ${testInfo.message || ''}`);

            if (testInfo.status === 'running' || testInfo.status === 'starting') {
                this.schedulePoll(testId);
            } else if (testInfo.status === 'completed') {
                const finalResults = await this.callBridgeAPI(`/api/test/${testId}`);
                if (finalResults.success && finalResults.test_info) {
                    this.testResults = finalResults.test_info;
                    this.showResults(this.testResults);
                    this.updateProgress(100, 'Test completed!');
                    this.isTestRunning = false;
                    this.updateUI();
                }
            } else if (['failed', 'timeout', 'stopped', 'disconnected', 'unknown'].includes(testInfo.status)) {
                this.handleTestStopped(`Test ended: ${testInfo.status}`);
            } else {
                this.handleTestStopped('Test ended (unknown status)');
            }
        } else {
            this.recordPollFailure(testId, result.error || 'Error fetching test status');
        }
    } catch (error) {
        console.error('Polling error:', error);
        this.recordPollFailure(testId, error.message);
    }
};

DiskBenchApp.prototype.schedulePoll = function(testId) {
    const cb = this.circuitBreaker;
    if (cb.pollTimerId) clearTimeout(cb.pollTimerId);
    cb.pollTimerId = setTimeout(() => this.pollTestStatus(testId), cb.currentIntervalMs);
};

DiskBenchApp.prototype.recordPollFailure = function(testId, errorMessage) {
    const cb = this.circuitBreaker;
    cb.consecutiveFailures++;
    cb.totalFailures++;
    cb.lastFailureTime = Date.now();

    console.warn(`Poll failure #${cb.consecutiveFailures} (total: ${cb.totalFailures}): ${errorMessage}`);

    if (cb.totalFailures >= cb.maxTotalRetries) {
        console.error(`Max retries (${cb.maxTotalRetries}) reached. Stopping polling.`);
        cb.state = 'open';
        this.isTestRunning = false;
        this.currentTestId = null;
        this.updateProgress(0, 'Server unreachable. Polling stopped after too many failures.');
        this.showConnectionWarning();
        this.updateUI();
        return;
    }

    if (cb.consecutiveFailures >= cb.maxConsecutiveFailures) {
        cb.state = 'open';
        console.warn('Circuit breaker tripped to OPEN state.');
        this.showConnectionWarning();
        this.updateProgressDetails(
            `Connection lost (${cb.consecutiveFailures} failures). Click "Reconnect" to retry.`
        );
        return;
    }

    cb.currentIntervalMs = Math.min(cb.currentIntervalMs * 2, cb.maxIntervalMs);
    this.updateProgressDetails(
        `Connection issue (attempt ${cb.consecutiveFailures}/${cb.maxConsecutiveFailures}). Retrying in ${Math.round(cb.currentIntervalMs / 1000)}s...`
    );
    this.schedulePoll(testId);
};

DiskBenchApp.prototype.resetCircuitBreaker = function() {
    const cb = this.circuitBreaker;
    cb.state = 'closed';
    cb.consecutiveFailures = 0;
    cb.totalFailures = 0;
    cb.currentIntervalMs = cb.baseIntervalMs;
    cb.lastFailureTime = null;
};

DiskBenchApp.prototype.attemptReconnect = function() {
    const cb = this.circuitBreaker;
    if (cb.state !== 'open') return;

    cb.state = 'half-open';
    cb.consecutiveFailures = 0;
    cb.currentIntervalMs = cb.baseIntervalMs;

    this.hideConnectionWarning();
    this.updateProgressDetails('Reconnecting to server...');

    const testId = this.currentTestId;
    if (testId) {
        this.pollTestStatus(testId);
    } else {
        this.callBridgeAPI('/api/status')
            .then(() => { this.resetCircuitBreaker(); this.hideConnectionWarning(); this.updateProgress(0, 'Server reconnected.'); })
            .catch(() => { cb.state = 'open'; cb.consecutiveFailures = cb.maxConsecutiveFailures; this.showConnectionWarning(); });
    }
};

DiskBenchApp.prototype.showConnectionWarning = function() {
    let banner = document.getElementById('connectionWarningBanner');
    if (!banner) {
        banner = document.createElement('div');
        banner.id = 'connectionWarningBanner';
        banner.className = 'connection-warning-banner';
        banner.innerHTML = `
            <div class="connection-warning-content">
                <div class="connection-warning-text">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>Server connection lost. Status polling has been suspended.</span>
                </div>
                <button id="reconnectBtn" class="btn btn-warning" onclick="window.app.attemptReconnect()">
                    <i class="fas fa-sync-alt"></i> Reconnect
                </button>
            </div>
        `;
        const progressSection = document.getElementById('progressSection');
        if (progressSection) {
            progressSection.insertBefore(banner, progressSection.firstChild.nextSibling);
        } else {
            document.body.prepend(banner);
        }
    }
    banner.classList.remove('hidden');
};

DiskBenchApp.prototype.hideConnectionWarning = function() {
    const banner = document.getElementById('connectionWarningBanner');
    if (banner) banner.classList.add('hidden');
};

// checkForActiveTest, showBackgroundTestNotice, checkFio are in app-test-control.js
