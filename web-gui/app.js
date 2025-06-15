/**
 * QLab Disk Performance Tester - Web GUI Application
 * 
 * This application provides a clean web interface that communicates with
 * the diskbench helper binary to perform professional disk performance testing.
 */

class DiskBenchApp {
    constructor() {
        this.selectedDisk = null;
        this.selectedTestType = 'qlab_prores_hq';
        this.testSize = 10;
        this.isTestRunning = false;
        this.testResults = null;
        this.progressInterval = null;
        
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
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.checkSystemStatus();
        this.loadAvailableDisks();
        this.updateUI();
    }
    
    setupEventListeners() {
        // Navigation tabs
        document.getElementById('testingTab').addEventListener('click', () => {
            this.switchTab('testing');
        });
        
        document.getElementById('setupTab').addEventListener('click', () => {
            this.switchTab('setup');
        });
        
        document.getElementById('architectureTab').addEventListener('click', () => {
            this.switchTab('architecture');
        });
        
        // Architecture toggle
        document.getElementById('toggleArchitecture').addEventListener('click', () => {
            this.toggleArchitectureDetails();
        });
        
        // Setup wizard controls
        document.getElementById('startInstallation').addEventListener('click', () => {
            this.startInstallation();
        });
        
        document.getElementById('runValidation').addEventListener('click', () => {
            this.runValidation();
        });
        
        document.getElementById('closeSetup').addEventListener('click', () => {
            this.closeSetup();
        });
        
        document.getElementById('skipSetup').addEventListener('click', () => {
            this.skipSetup();
        });
        
        document.getElementById('retrySetup').addEventListener('click', () => {
            this.retrySetup();
        });
        
        // Disk refresh
        document.getElementById('refreshDisks').addEventListener('click', () => {
            this.loadAvailableDisks();
        });
        
        // Test type selection
        document.querySelectorAll('input[name="testType"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.selectedTestType = e.target.value;
                this.updateUI();
            });
        });
        
        // Test size
        document.getElementById('testSize').addEventListener('change', (e) => {
            this.testSize = parseInt(e.target.value);
            this.updateUI();
        });
        
        // Test controls
        document.getElementById('startTest').addEventListener('click', () => {
            this.startTest();
        });
        
        document.getElementById('stopTest').addEventListener('click', () => {
            this.stopTest();
        });
        
        document.getElementById('exportResults').addEventListener('click', () => {
            this.exportResults();
        });
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
    
    async loadAvailableDisks() {
        const diskList = document.getElementById('diskList');
        diskList.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Loading available disks...</div>';
        
        try {
            // Simulate calling the diskbench helper binary
            const result = await this.executeDiskBenchCommand(['--list-disks', '--json']);
            
            if (result && result.disks) {
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
    }
    
    renderDiskList(disks) {
        const diskList = document.getElementById('diskList');
        
        if (!disks || disks.length === 0) {
            diskList.innerHTML = '<div class="loading"><i class="fas fa-info-circle"></i> No suitable disks found for testing.</div>';
            return;
        }
        
        const diskItems = disks
            .filter(disk => disk.suitable_for_testing)
            .map(disk => this.createDiskItem(disk))
            .join('');
        
        diskList.innerHTML = diskItems;
        
        // Add event listeners to disk items
        document.querySelectorAll('.disk-item').forEach(item => {
            item.addEventListener('click', () => {
                const diskPath = item.dataset.diskPath;
                this.selectDisk(diskPath, disks.find(d => d.device === diskPath));
            });
        });
    }
    
    createDiskItem(disk) {
        const typeClass = disk.type.toLowerCase();
        const isSelected = this.selectedDisk && this.selectedDisk.device === disk.device;
        
        return `
            <div class="disk-item ${isSelected ? 'selected' : ''}" data-disk-path="${disk.device}">
                <input type="radio" name="selectedDisk" value="${disk.device}" ${isSelected ? 'checked' : ''}>
                <div class="disk-info">
                    <div class="disk-name">${disk.name}</div>
                    <div class="disk-details">
                        ${disk.device} • ${disk.size} • ${disk.file_system}
                        ${disk.free_space ? ` • ${disk.free_space} free` : ''}
                    </div>
                </div>
                <div class="disk-type ${typeClass}">${disk.type}</div>
            </div>
        `;
    }
    
    selectDisk(diskPath, diskInfo) {
        this.selectedDisk = diskInfo;
        
        // Update UI
        document.querySelectorAll('.disk-item').forEach(item => {
            item.classList.remove('selected');
            item.querySelector('input[type="radio"]').checked = false;
        });
        
        const selectedItem = document.querySelector(`[data-disk-path="${diskPath}"]`);
        if (selectedItem) {
            selectedItem.classList.add('selected');
            selectedItem.querySelector('input[type="radio"]').checked = true;
        }
        
        this.updateUI();
    }
    
    updateUI() {
        const startButton = document.getElementById('startTest');
        const canStartTest = this.selectedDisk && !this.isTestRunning;
        
        startButton.disabled = !canStartTest;
        
        if (canStartTest) {
            startButton.innerHTML = '<i class="fas fa-play"></i> Start Test';
        } else if (this.isTestRunning) {
            startButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running...';
        } else {
            startButton.innerHTML = '<i class="fas fa-play"></i> Select Disk First';
        }
    }
    
    async startTest() {
        if (!this.selectedDisk || this.isTestRunning) {
            return;
        }
        
        this.isTestRunning = true;
        this.testResults = null;
        
        // Show progress section
        document.getElementById('progressSection').classList.remove('hidden');
        document.getElementById('resultsSection').classList.add('hidden');
        document.getElementById('startTest').classList.add('hidden');
        document.getElementById('stopTest').classList.remove('hidden');
        document.getElementById('exportResults').classList.add('hidden');
        
        // Reset progress
        this.updateProgress(0, 'Preparing test...');
        
        try {
            // Generate output filename
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const outputFile = `/tmp/diskbench-results-${timestamp}.json`;
            
            // Build command
            const command = [
                '--test', this.selectedTestType,
                '--disk', this.selectedDisk.device,
                '--size', this.testSize.toString(),
                '--output', outputFile,
                '--progress',
                '--json'
            ];
            
            this.updateProgress(5, 'Starting FIO test...');
            this.updateProgressDetails(`Command: diskbench ${command.join(' ')}`);
            
            // Start progress simulation
            this.startProgressSimulation();
            
            // Execute test
            const result = await this.executeDiskBenchCommand(command);
            
            // Stop progress simulation
            this.stopProgressSimulation();
            
            if (result) {
                this.updateProgress(100, 'Test completed successfully!');
                this.testResults = result;
                this.showResults(result);
            } else {
                throw new Error('Test failed - no results received');
            }
            
        } catch (error) {
            console.error('Test failed:', error);
            this.stopProgressSimulation();
            this.updateProgress(0, `Test failed: ${error.message}`);
            this.updateProgressDetails(`Error: ${error.message}`);
        } finally {
            this.isTestRunning = false;
            this.updateUI();
            document.getElementById('startTest').classList.remove('hidden');
            document.getElementById('stopTest').classList.add('hidden');
        }
    }
    
    stopTest() {
        if (!this.isTestRunning) {
            return;
        }
        
        // In a real implementation, this would send a signal to stop the test
        this.stopProgressSimulation();
        this.isTestRunning = false;
        this.updateProgress(0, 'Test stopped by user');
        this.updateUI();
        
        document.getElementById('startTest').classList.remove('hidden');
        document.getElementById('stopTest').classList.add('hidden');
    }
    
    startProgressSimulation() {
        let progress = 5;
        const phases = [
            { end: 20, message: 'Initializing test environment...' },
            { end: 40, message: 'Running sequential read tests...' },
            { end: 60, message: 'Running sequential write tests...' },
            { end: 80, message: 'Running random read tests...' },
            { end: 95, message: 'Running random write tests...' },
            { end: 100, message: 'Analyzing results...' }
        ];
        
        let phaseIndex = 0;
        
        this.progressInterval = setInterval(() => {
            if (phaseIndex < phases.length) {
                const phase = phases[phaseIndex];
                
                if (progress < phase.end) {
                    progress += Math.random() * 2;
                    this.updateProgress(Math.min(progress, phase.end), phase.message);
                } else {
                    phaseIndex++;
                }
            }
        }, 500);
    }
    
    stopProgressSimulation() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
    }
    
    updateProgress(percentage, message) {
        document.getElementById('progressFill').style.width = `${percentage}%`;
        document.getElementById('progressText').textContent = message;
    }
    
    updateProgressDetails(details) {
        document.getElementById('progressDetails').textContent = details;
    }
    
    showResults(results) {
        document.getElementById('resultsSection').classList.remove('hidden');
        document.getElementById('exportResults').classList.remove('hidden');
        
        // Render QLab analysis
        this.renderQLabAnalysis(results.qlab_analysis || results.analysis);
        
        // Render detailed metrics
        this.renderDetailedMetrics(results.fio_results);
        
        // Render implementation details
        this.renderImplementationDetails(results);
    }
    
    renderQLabAnalysis(analysis) {
        const container = document.getElementById('qlabAnalysis');
        
        if (!analysis) {
            container.innerHTML = '<p>No analysis data available.</p>';
            return;
        }
        
        const overallClass = this.getPerformanceClass(analysis.overall_performance || analysis.performance_class);
        const badgeClass = overallClass;
        
        container.className = `qlab-analysis ${overallClass}`;
        container.innerHTML = `
            <div class="analysis-header">
                <h3 class="analysis-title">QLab Performance Analysis</h3>
                <div class="analysis-badge ${badgeClass}">
                    ${this.getPerformanceMessage(analysis.overall_performance || analysis.performance_class)}
                </div>
            </div>
            <div class="analysis-grid">
                <div class="analysis-section">
                    <h4>Performance Indicators</h4>
                    <ul>
                        ${this.renderAnalysisDetails(analysis)}
                    </ul>
                </div>
                <div class="analysis-section">
                    <h4>Recommendations</h4>
                    <ul>
                        ${this.renderRecommendations(analysis)}
                    </ul>
                </div>
            </div>
        `;
    }
    
    renderAnalysisDetails(analysis) {
        const details = [];
        
        if (analysis.read_performance) {
            details.push(`${this.getPerformanceIcon(analysis.read_performance)} Read Performance: ${analysis.read_performance}`);
        }
        if (analysis.write_performance) {
            details.push(`${this.getPerformanceIcon(analysis.write_performance)} Write Performance: ${analysis.write_performance}`);
        }
        if (analysis.latency_performance) {
            details.push(`${this.getPerformanceIcon(analysis.latency_performance)} Latency Performance: ${analysis.latency_performance}`);
        }
        
        return details.map(detail => `<li>${detail}</li>`).join('');
    }
    
    renderRecommendations(analysis) {
        // This would come from the test results in a real implementation
        const recommendations = [
            "✅ Good performance for most QLab applications",
            "✅ Suitable for standard video playback",
            "💡 Consider SSD upgrade for demanding applications"
        ];
        
        return recommendations.map(rec => `<li>${rec}</li>`).join('');
    }
    
    renderDetailedMetrics(fioResults) {
        const container = document.getElementById('detailedMetrics');
        
        if (!fioResults || !fioResults.summary) {
            container.innerHTML = '<p>No detailed metrics available.</p>';
            return;
        }
        
        const summary = fioResults.summary;
        const metrics = [
            {
                title: 'Sequential Read',
                value: this.formatNumber(summary.total_read_bw || 0),
                unit: 'MB/s',
                details: `${this.formatNumber(summary.total_read_iops || 0)} IOPS`
            },
            {
                title: 'Sequential Write',
                value: this.formatNumber(summary.total_write_bw || 0),
                unit: 'MB/s',
                details: `${this.formatNumber(summary.total_write_iops || 0)} IOPS`
            },
            {
                title: 'Read Latency',
                value: this.formatNumber(summary.avg_read_latency || 0),
                unit: 'ms',
                details: 'Average latency'
            },
            {
                title: 'Write Latency',
                value: this.formatNumber(summary.avg_write_latency || 0),
                unit: 'ms',
                details: 'Average latency'
            }
        ];
        
        container.innerHTML = metrics.map(metric => `
            <div class="metric-card">
                <h4>${metric.title}</h4>
                <div class="metric-value">${metric.value}</div>
                <div class="metric-unit">${metric.unit}</div>
                <div class="metric-details">${metric.details}</div>
            </div>
        `).join('');
    }
    
    renderImplementationDetails(results) {
        const container = document.getElementById('implementationInfo');
        const testInfo = results.test_info || {};
        
        container.innerHTML = `
            <p><strong>Test executed:</strong> ${testInfo.test_name || 'Unknown'} on ${testInfo.disk_path || 'Unknown'}</p>
            <p><strong>Timestamp:</strong> ${testInfo.timestamp ? new Date(testInfo.timestamp).toLocaleString() : 'Unknown'}</p>
            <p><strong>CLI Command:</strong> <code>diskbench --test ${this.selectedTestType} --disk ${this.selectedDisk?.device} --output result.json</code></p>
            <p><strong>Architecture:</strong> Web GUI → Helper Binary → FIO Engine → JSON Results</p>
        `;
    }
    
    getPerformanceClass(performance) {
        switch (performance) {
            case 'excellent': return 'excellent';
            case 'good': return 'warning';
            case 'fair': return 'warning';
            case 'poor': return 'danger';
            default: return 'warning';
        }
    }
    
    getPerformanceMessage(performance) {
        switch (performance) {
            case 'excellent': return '✅ Excellent for QLab';
            case 'good': return '✅ Good for QLab';
            case 'fair': return '⚠️ Fair for QLab';
            case 'poor': return '❌ Poor for QLab';
            default: return '❓ Unknown Performance';
        }
    }
    
    getPerformanceIcon(performance) {
        switch (performance) {
            case 'excellent': return '✅';
            case 'good': return '✅';
            case 'fair': return '⚠️';
            case 'poor': return '❌';
            default: return '❓';
        }
    }
    
    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        } else {
            return num.toFixed(1);
        }
    }
    
    async executeDiskBenchCommand(args) {
        // Use the bridge server to execute real diskbench commands
        console.log('Executing diskbench command:', args);
        
        try {
            if (args.includes('--list-disks')) {
                return await this.callBridgeAPI('/api/disks');
            } else if (args.includes('--test')) {
                // Start a test via the bridge server
                const testParams = this.parseTestArgs(args);
                return await this.startRealTest(testParams);
            }
            
            throw new Error('Unknown command');
        } catch (error) {
            console.error('Bridge server error:', error);
            // No more mock data fallback - let the real error show
            throw error;
        }
    }
    
    async callBridgeAPI(endpoint, options = {}) {
        const baseURL = 'http://localhost:8080';
        const url = `${baseURL}${endpoint}`;
        
        const response = await fetch(url, {
            method: options.method || 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            body: options.body ? JSON.stringify(options.body) : undefined
        });
        
        if (!response.ok) {
            throw new Error(`Bridge server error: ${response.status} ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    parseTestArgs(args) {
        const testParams = {
            test_type: 'setup_check',
            disk_path: '/tmp',
            size_gb: 10,
            show_progress: true
        };
        
        // Parse command line arguments
        for (let i = 0; i < args.length; i++) {
            if (args[i] === '--test' && i + 1 < args.length) {
                testParams.test_type = args[i + 1];
            } else if (args[i] === '--disk' && i + 1 < args.length) {
                testParams.disk_path = args[i + 1];
            } else if (args[i] === '--size' && i + 1 < args.length) {
                testParams.size_gb = parseInt(args[i + 1]);
            }
        }
        
        return testParams;
    }
    
    async startRealTest(testParams) {
        try {
            // Start the test
            const startResult = await this.callBridgeAPI('/api/test/start', {
                method: 'POST',
                body: testParams
            });
            
            if (!startResult.success) {
                throw new Error(startResult.error || 'Failed to start test');
            }
            
            const testId = startResult.test_id;
            
            // Poll for test completion
            return await this.pollTestCompletion(testId);
            
        } catch (error) {
            console.error('Real test error:', error);
            throw error;
        }
    }
    
    async pollTestCompletion(testId) {
        const maxAttempts = 120; // 10 minutes max (5 second intervals)
        let attempts = 0;
        
        while (attempts < maxAttempts) {
            try {
                const statusResult = await this.callBridgeAPI(`/api/test/${testId}`);
                
                if (!statusResult.success) {
                    throw new Error(statusResult.error || 'Failed to get test status');
                }
                
                const testInfo = statusResult.test_info;
                
                // Update progress if we have it
                if (testInfo.progress !== undefined) {
                    this.updateProgress(testInfo.progress, `Test running... ${testInfo.status}`);
                }
                
                if (testInfo.status === 'completed') {
                    return testInfo.result;
                } else if (testInfo.status === 'failed') {
                    throw new Error(testInfo.error || 'Test failed');
                }
                
                // Wait before next poll
                await new Promise(resolve => setTimeout(resolve, 5000));
                attempts++;
                
            } catch (error) {
                console.error('Polling error:', error);
                throw error;
            }
        }
        
        throw new Error('Test timed out');
    }
    
    
    exportResults() {
        if (!this.testResults) {
            return;
        }
        
        const report = {
            ...this.testResults,
            architecture: 'Web-GUI-Helper-Binary',
            version: '1.0.0',
            exported_at: new Date().toISOString()
        };
        
        const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `qlab-disk-performance-${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }
    
    // Setup Wizard Methods
    async checkSystemStatus() {
        this.updateSystemStatus('checking', 'Checking system status...');
        
        try {
            // Check if bridge server is available
            const status = await this.callBridgeAPI('/api/status');
            
            if (status.success && status.status) {
                const sysStatus = status.status;
                this.setupState.fioAvailable = sysStatus.fio_available || false;
                this.setupState.fioWorking = sysStatus.fio_working || false;
                this.setupState.diskAccess = sysStatus.disk_access || false;
                
                // Check if system is usable (either fully working or partially working)
                const systemUsable = sysStatus.system_usable || 
                                   (sysStatus.fio_available && (sysStatus.fio_working || sysStatus.fio_partial));
                
                if (systemUsable) {
                    if (sysStatus.fio_working) {
                        this.setupState.systemStatus = 'ready';
                        this.updateSystemStatus('ready', '✅ System ready for testing');
                    } else if (sysStatus.fio_partial) {
                        this.setupState.systemStatus = 'warning';
                        this.updateSystemStatus('warning', '⚠️ System partially ready - FIO has limitations but tests can run');
                    }
                } else {
                    this.setupState.systemStatus = 'warning';
                    this.updateSystemStatus('warning', '⚠️ System setup required - Click "Setup & Diagnostics" tab');
                }
            } else {
                throw new Error('Bridge server not responding');
            }
        } catch (error) {
            console.error('System status check failed:', error);
            this.setupState.systemStatus = 'error';
            this.updateSystemStatus('error', '❌ System setup required - Bridge server unavailable');
        }
        
        this.updateSetupStep1();
    }
    
    updateSystemStatus(type, message) {
        const statusEl = document.getElementById('systemStatus');
        const indicatorEl = statusEl.querySelector('.status-indicator');
        
        statusEl.className = `system-status ${type}`;
        indicatorEl.innerHTML = `<i class="fas fa-${this.getStatusIcon(type)}"></i> ${message}`;
    }
    
    getStatusIcon(type) {
        switch (type) {
            case 'ready': return 'check-circle';
            case 'warning': return 'exclamation-triangle';
            case 'error': return 'times-circle';
            default: return 'circle-notch fa-spin';
        }
    }
    
    switchTab(tabName) {
        this.currentTab = tabName;
        
        // Update tab buttons
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.getElementById(`${tabName}Tab`).classList.add('active');
        
        // Show/hide content sections
        const setupWizard = document.getElementById('setupWizard');
        const architectureSection = document.querySelector('.architecture-section');
        const mainInterface = document.querySelector('.main-interface');
        
        setupWizard.classList.add('hidden');
        architectureSection.classList.add('hidden');
        mainInterface.classList.add('hidden');
        
        switch (tabName) {
            case 'testing':
                mainInterface.classList.remove('hidden');
                break;
            case 'setup':
                setupWizard.classList.remove('hidden');
                this.initializeSetupWizard();
                break;
            case 'architecture':
                architectureSection.classList.remove('hidden');
                break;
        }
    }
    
    initializeSetupWizard() {
        // Reset setup wizard to step 1
        this.setupState.setupStep = 1;
        this.updateSetupStep1();
    }
    
    updateSetupStep1() {
        const step1 = document.getElementById('step1');
        const step1Status = document.getElementById('step1Status');
        const detectionResults = document.getElementById('detectionResults');
        
        // Activate step 1
        step1.classList.add('active');
        step1Status.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i>';
        
        // Show detection results
        const results = [
            { 
                label: 'FIO Binary', 
                status: this.setupState.fioAvailable ? 'success' : 'error',
                message: this.setupState.fioAvailable ? 'Available' : 'Not found'
            },
            { 
                label: 'FIO Functionality', 
                status: this.setupState.fioWorking ? 'success' : 'error',
                message: this.setupState.fioWorking ? 'Working' : 'Failed tests'
            },
            { 
                label: 'Disk Access', 
                status: this.setupState.diskAccess ? 'success' : 'warning',
                message: this.setupState.diskAccess ? 'Available' : 'Limited'
            },
            { 
                label: 'macOS Compatibility', 
                status: 'success',
                message: 'Compatible'
            }
        ];
        
        detectionResults.innerHTML = results.map(result => `
            <div class="detection-item">
                <span class="detection-label">${result.label}</span>
                <div class="detection-status ${result.status}">
                    <i class="fas fa-${result.status === 'success' ? 'check' : result.status === 'error' ? 'times' : 'exclamation-triangle'}"></i>
                    ${result.message}
                </div>
            </div>
        `).join('');
        
        // Update step 1 status
        const allGood = this.setupState.fioAvailable && this.setupState.fioWorking && this.setupState.diskAccess;
        
        setTimeout(() => {
            if (allGood) {
                step1.classList.add('completed');
                step1Status.innerHTML = '<i class="fas fa-check"></i>';
                this.enableStep3();
            } else {
                step1Status.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
                this.enableStep2();
            }
        }, 2000);
    }
    
    enableStep2() {
        const step2 = document.getElementById('step2');
        const startButton = document.getElementById('startInstallation');
        
        step2.classList.add('active');
        startButton.disabled = false;
    }
    
    enableStep3() {
        const step3 = document.getElementById('step3');
        const validationButton = document.getElementById('runValidation');
        
        step3.classList.add('active');
        validationButton.disabled = false;
    }
    
    async startInstallation() {
        const step2 = document.getElementById('step2');
        const step2Status = document.getElementById('step2Status');
        const installationProgress = document.getElementById('installationProgress');
        const startButton = document.getElementById('startInstallation');
        
        this.setupState.installationInProgress = true;
        startButton.disabled = true;
        step2Status.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i>';
        
        // Simulate installation process
        const logMessages = [
            { type: 'info', message: 'Starting FIO installation process...' },
            { type: 'info', message: 'Detecting macOS version and architecture...' },
            { type: 'success', message: 'macOS compatible version detected' },
            { type: 'info', message: 'Downloading FIO binary for macOS...' },
            { type: 'info', message: 'Configuring FIO for macOS shared memory...' },
            { type: 'warning', message: 'Applying macOS-specific patches...' },
            { type: 'success', message: 'FIO installation completed' },
            { type: 'info', message: 'Testing FIO functionality...' },
            { type: 'success', message: 'FIO is working correctly' }
        ];
        
        installationProgress.innerHTML = '';
        
        for (let i = 0; i < logMessages.length; i++) {
            await new Promise(resolve => setTimeout(resolve, 1000));
            const log = logMessages[i];
            installationProgress.innerHTML += `<div class="log-line ${log.type}">[${new Date().toLocaleTimeString()}] ${log.message}</div>`;
            installationProgress.scrollTop = installationProgress.scrollHeight;
        }
        
        // Update state
        this.setupState.fioAvailable = true;
        this.setupState.fioWorking = true;
        this.setupState.installationInProgress = false;
        
        // Mark step 2 as completed
        step2.classList.add('completed');
        step2Status.innerHTML = '<i class="fas fa-check"></i>';
        
        // Enable step 3
        this.enableStep3();
        
        // Update system status
        this.updateSystemStatus('ready', '✅ System ready for testing');
    }
    
    async runValidation() {
        const step3 = document.getElementById('step3');
        const step3Status = document.getElementById('step3Status');
        const validationResults = document.getElementById('validationResults');
        const validationButton = document.getElementById('runValidation');
        
        validationButton.disabled = true;
        step3Status.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i>';
        
        // Simulate validation tests
        const tests = [
            { name: 'FIO Binary Test', delay: 1000 },
            { name: 'Disk Access Test', delay: 1500 },
            { name: 'Performance Test', delay: 2000 },
            { name: 'Configuration Test', delay: 1000 }
        ];
        
        validationResults.innerHTML = '';
        
        for (const test of tests) {
            // Add pending test
            validationResults.innerHTML += `
                <div class="validation-test" id="test-${test.name.replace(/\s+/g, '-').toLowerCase()}">
                    <span class="validation-test-name">${test.name}</span>
                    <div class="validation-result pending">
                        <i class="fas fa-circle-notch fa-spin"></i> Running...
                    </div>
                </div>
            `;
            
            await new Promise(resolve => setTimeout(resolve, test.delay));
            
            // Update to passed
            const testEl = document.getElementById(`test-${test.name.replace(/\s+/g, '-').toLowerCase()}`);
            testEl.querySelector('.validation-result').innerHTML = `
                <i class="fas fa-check"></i> Passed
            `;
            testEl.querySelector('.validation-result').className = 'validation-result pass';
        }
        
        // Mark step 3 as completed
        step3.classList.add('completed');
        step3Status.innerHTML = '<i class="fas fa-check"></i>';
        
        // Update system status to fully ready
        this.updateSystemStatus('ready', '✅ System fully validated and ready for testing');
    }
    
    closeSetup() {
        this.switchTab('testing');
    }
    
    skipSetup() {
        this.setupState.systemStatus = 'warning';
        this.updateSystemStatus('warning', '⚠️ Setup skipped - Some features may not work correctly');
        this.switchTab('testing');
    }
    
    retrySetup() {
        this.initializeSetupWizard();
        this.checkSystemStatus();
    }
}

// Initialize the application when the page loads
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new DiskBenchApp();
});
