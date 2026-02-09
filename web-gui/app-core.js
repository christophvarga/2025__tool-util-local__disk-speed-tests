/**
 * QLab Disk Performance Tester - Core Module
 * Class definition, constructor, init, event listeners, utilities.
 */

class DiskBenchApp {
    static BRIDGE_URL = 'http://localhost:8765';
    static API_TIMEOUT_MS = 30000;

    constructor() {
        this.selectedDisk = null;
        this.selectedTestType = null;
        this.testSize = 10;
        this.isTestRunning = false;
        this.testResults = null;
        this.currentTestId = null;
        this.currentTestDuration = 0;

        // Setup wizard state
        this.currentTab = 'testing';
        this.setupState = {
            systemStatus: 'checking',
            fioAvailable: false,
            fioWorking: false,
            diskAccess: false,
            setupStep: 1,
            installationInProgress: false
        };

        // Circuit breaker for status polling
        this.circuitBreaker = {
            state: 'closed',
            consecutiveFailures: 0,
            totalFailures: 0,
            maxConsecutiveFailures: 5,
            maxTotalRetries: 30,
            currentIntervalMs: 2000,
            baseIntervalMs: 2000,
            maxIntervalMs: 30000,
            lastFailureTime: null,
            pollTimerId: null,
        };

        this.init();
    }

    _escapeHTML(str) {
        const div = document.createElement('div');
        div.textContent = String(str ?? '');
        return div.innerHTML;
    }

    init() {
        this.loadPersistedState();
        this.setupEventListeners();
        this.checkSystemStatus();
        this.loadAvailableDisks();
        this.loadCustomTests();
        this.loadTests();
        this.checkForActiveTest();
        this.initializeCharts();
        this.setupKeyboardShortcuts();
        this.updateUI();
    }

    setupEventListeners() {
        document.getElementById('testingTab').addEventListener('click', () => this.switchTab('testing'));
        document.getElementById('setupTab').addEventListener('click', () => this.switchTab('setup'));
        document.getElementById('architectureTab').addEventListener('click', () => this.switchTab('architecture'));
        document.getElementById('toggleArchitecture').addEventListener('click', () => this.toggleArchitectureDetails());
        document.getElementById('startInstallation').addEventListener('click', () => this.startInstallation());
        document.getElementById('runValidation').addEventListener('click', () => this.runValidation());
        document.getElementById('closeSetup').addEventListener('click', () => this.closeSetup());
        document.getElementById('skipSetup').addEventListener('click', () => this.skipSetup());
        document.getElementById('retrySetup').addEventListener('click', () => this.retrySetup());
        document.getElementById('refreshDisks').addEventListener('click', () => this.loadAvailableDisks());

        // Disk alias controls
        const aliasInput = document.getElementById('diskAliasInput');
        const saveAliasBtn = document.getElementById('saveDiskAlias');
        const aliasStatus = document.getElementById('diskAliasStatus');

        if (saveAliasBtn) {
            saveAliasBtn.addEventListener('click', () => {
                if (!this.selectedDisk) return;
                const alias = aliasInput ? aliasInput.value.trim() : '';
                this.setDiskAlias(this.selectedDisk.device, alias);
                if (aliasStatus) {
                    aliasStatus.classList.remove('hidden');
                    aliasStatus.textContent = 'Saved';
                    setTimeout(() => aliasStatus.classList.add('hidden'), 1200);
                }
                if (this.availableDisks) this.renderDiskList(this.availableDisks);
            });
        }
        if (aliasInput) {
            aliasInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && this.selectedDisk) {
                    e.preventDefault();
                    const alias = aliasInput.value.trim();
                    this.setDiskAlias(this.selectedDisk.device, alias);
                    if (aliasStatus) {
                        aliasStatus.classList.remove('hidden');
                        aliasStatus.textContent = 'Saved';
                        setTimeout(() => aliasStatus.classList.add('hidden'), 1200);
                    }
                    if (this.availableDisks) this.renderDiskList(this.availableDisks);
                }
            });
        }

        this.bindTestTypeListeners();

        document.getElementById('testSize').addEventListener('change', (e) => {
            this.testSize = parseInt(e.target.value);
            this.updateUI();
        });

        document.getElementById('startTest').addEventListener('click', () => this.startTest());
        document.getElementById('stopTest').addEventListener('click', () => this.stopTest());
        document.getElementById('stopAllTests').addEventListener('click', () => this.stopAllTests());
        document.getElementById('exportResults').addEventListener('click', () => this.exportResults());

        const copyBtn = document.getElementById('copyResults');
        if (copyBtn) copyBtn.addEventListener('click', () => this.copyResults());

        const copyCliBtn = document.getElementById('copyCli');
        if (copyCliBtn) copyCliBtn.addEventListener('click', () => this.copyCli());

        const downloadSummaryBtn = document.getElementById('downloadSummary');
        if (downloadSummaryBtn) downloadSummaryBtn.addEventListener('click', () => this.downloadSummary());

        const createCustomBtn = document.getElementById('createCustomTestBtn');
        if (createCustomBtn) createCustomBtn.addEventListener('click', () => this.openCustomTestModal());

        document.getElementById('closeCustomTestModal').addEventListener('click', () => this.closeCustomTestModal());
        document.getElementById('cancelCustomTest').addEventListener('click', () => this.closeCustomTestModal());
        document.getElementById('saveCustomTest').addEventListener('click', () => this.saveCustomTest());

        document.getElementById('customRwMix').addEventListener('input', (e) => {
            document.getElementById('rwMixValue').textContent = e.target.value;
        });
    }

    initializeCharts() {
        const ctx = document.getElementById('bandwidthChart');
        if (!ctx) return;
        this.bandwidthChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Read MB/s', data: [],
                    borderColor: 'rgb(75, 192, 192)', tension: 0.1, fill: false
                }, {
                    label: 'Write MB/s', data: [],
                    borderColor: 'rgb(255, 99, 132)', tension: 0.1, fill: false
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false, animation: false,
                scales: {
                    y: { beginAtZero: true, title: { display: true, text: 'Bandwidth (MB/s)' } },
                    x: { display: false }
                },
                plugins: { legend: { display: true, position: 'top' } }
            }
        });
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
                if (!this.isTestRunning && this.selectedDisk) { e.preventDefault(); this.startTest(); }
            }
            if (e.key === 'Escape' && this.isTestRunning) {
                e.preventDefault();
                if (confirm('Stop the running test?')) this.stopTest();
            }
            if ((e.metaKey || e.ctrlKey) && e.key === 'r') {
                e.preventDefault(); this.loadAvailableDisks();
            }
        });
    }

    updateUI() {
        const startButton = document.getElementById('startTest');
        const stopButton = document.getElementById('stopTest');
        const stopAllButton = document.getElementById('stopAllTests');
        const canStartTest = this.selectedDisk && !this.isTestRunning;

        startButton.disabled = !canStartTest;
        if (canStartTest) {
            startButton.innerHTML = '<i class="fas fa-play"></i> Start Test';
            stopButton.classList.add('hidden');
            stopAllButton.classList.add('hidden');
        } else if (this.isTestRunning) {
            startButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running...';
            stopButton.classList.remove('hidden');
            stopAllButton.classList.add('hidden');
        } else {
            startButton.innerHTML = '<i class="fas fa-play"></i> Select Disk First';
            stopButton.classList.add('hidden');
            stopAllButton.classList.add('hidden');
        }
    }

    switchTab(tabId) {
        document.querySelectorAll('.tab-content').forEach(s => s.classList.add('hidden'));
        document.getElementById(`${tabId}Section`).classList.remove('hidden');
        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        document.getElementById(`${tabId}Tab`).classList.add('active');
        this.currentTab = tabId;
        if (tabId === 'setup') this.updateSetupUI();
    }

    toggleArchitectureDetails() {
        const details = document.getElementById('architectureDetails');
        const button = document.getElementById('toggleArchitecture');
        if (details.classList.contains('hidden')) {
            details.classList.remove('hidden');
            button.innerHTML = '<i class="fas fa-info-circle"></i> Hide Architecture Details';
        } else {
            details.classList.add('hidden');
            button.innerHTML = '<i class="fas fa-info-circle"></i> Show Architecture Details';
        }
    }

    bindTestTypeListeners() {
        document.querySelectorAll('input[name="testType"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.selectedTestType = e.target.value;
                this.updateUI();
                this.updateTestDescription();
            });
        });
    }

    // ----- Utility methods -----
    formatNumber(num) {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toFixed(1);
    }

    formatDuration(seconds) {
        if (!seconds || seconds < 0) return '--:--';
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        if (hours > 0) return `${hours}h ${minutes}m`;
        if (minutes > 0) return `${minutes}m ${secs}s`;
        return `${secs}s`;
    }

    getPerformanceClass(p) {
        const map = { 'excellent': 'excellent', 'good': 'warning', 'fair': 'warning', 'poor': 'danger' };
        return map[p] || 'warning';
    }

    getPerformanceMessage(p) {
        const map = { 'excellent': '✅ Excellent for QLab', 'good': '✅ Good for QLab', 'fair': '⚠️ Fair for QLab', 'poor': '❌ Poor for QLab' };
        return map[p] || '❓ Unknown Performance';
    }

    getPerformanceIcon(p) {
        const map = { 'excellent': '✅', 'good': '✅', 'fair': '⚠️', 'poor': '❌' };
        return map[p] || '❓';
    }

    getLatencyClass(latency) {
        if (latency <= 2) return 'excellent';
        if (latency <= 5) return 'good';
        if (latency <= 10) return 'warning';
        return 'danger';
    }

    getQLabPerformanceTier(currentBW, requiredBW) {
        if (currentBW >= requiredBW * 1.2) return { tier: 'FLAGSHIP', message: '✅ Excellent for QLab', class: 'excellent' };
        if (currentBW >= requiredBW * 1.05) return { tier: 'PROFESSIONAL', message: '✅ Good for QLab', class: 'good' };
        if (currentBW >= requiredBW) return { tier: 'STANDARD', message: '⚠️ Fair for QLab', class: 'warning' };
        return { tier: 'BASIC', message: '❌ Poor for QLab', class: 'danger' };
    }

    getTestDisplayName(testType) {
        const names = {
            'quick_max_speed': 'Quick Max Speed Test',
            'qlab_prores_422_show': 'ProRes 422 Show Simulation',
            'qlab_prores_hq_show': 'ProRes HQ Show Simulation',
            'thermal_maximum_analyser': 'Thermal Maximum Analyser'
        };
        return names[testType] || testType;
    }

    sanitizeForFileName(name) {
        return (name || 'unknown').replace(/[^a-zA-Z0-9._-]+/g, '_').replace(/_+/g, '_').replace(/^_+|_+$/g, '');
    }
}
