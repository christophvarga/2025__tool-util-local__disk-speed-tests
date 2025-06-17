/**
 * QLab Disk Performance Tester - Web GUI Application
 * 
 * This application provides a clean web interface that communicates with
 * the diskbench helper binary to perform professional disk performance testing.
 */

class DiskBenchApp {
    constructor() {
        this.selectedDisk = null;
        this.selectedTestType = 'qlab_prores_422_show';
        this.testSize = 10;
        this.isTestRunning = false;
        this.testResults = null;
        this.currentTestId = null; // Added to track the running test ID
        
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
        
        document.getElementById('stopAllTests').addEventListener('click', () => {
            this.stopAllTests();
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
            document.getElementById('stopAllTests').classList.add('hidden'); // Hide stop all button when not running
        } else if (this.isTestRunning) {
            startButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running...';
            document.getElementById('stopAllTests').classList.remove('hidden'); // Show stop all button when running
        } else {
            startButton.innerHTML = '<i class="fas fa-play"></i> Select Disk First';
            document.getElementById('stopAllTests').classList.add('hidden'); // Hide stop all button when not running
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
        document.getElementById('stopAllTests').classList.remove('hidden'); // Show stop all button
        document.getElementById('exportResults').classList.add('hidden');
        
        // Temperature monitoring removed - no longer needed
        
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
            
            // Execute test
            const result = await this.executeDiskBenchCommand(command);
            
            if (result) {
                this.updateProgress(100, 'Test completed successfully!');
                this.testResults = result;
                this.showResults(result);
            } else {
                throw new Error('Test failed - no results received');
            }
            
        } catch (error) {
            console.error('Test failed:', error);
            this.updateProgress(0, `Test failed: ${error.message}`);
            this.updateProgressDetails(`Error: ${error.message}`);
        } finally {
            this.isTestRunning = false;
            
            this.updateUI();
            document.getElementById('startTest').classList.remove('hidden');
            document.getElementById('stopTest').classList.add('hidden');
            document.getElementById('stopAllTests').classList.add('hidden'); // Hide stop all button
        }
    }
    
    async stopTest() {
        if (!this.isTestRunning || !this.currentTestId) {
            return;
        }
        
        try {
            // Actually call the bridge server to stop the test
            const result = await this.callBridgeAPI(`/api/test/stop/${this.currentTestId}`, {
                method: 'POST'
            });
            
            if (result.success) {
                this.handleTestStopped('Test stopped by user');
            } else {
                throw new Error(result.error || 'Failed to stop test');
            }
        } catch (error) {
            console.error('Stop test failed:', error);
            this.handleTestStopped(`Stop failed: ${error.message}`);
        }
    }
    
    handleTestStopped(message) {
        this.isTestRunning = false;
        this.currentTestId = null; // Clear the test ID
        this.updateProgress(0, message);
        this.updateUI();
        
        document.getElementById('startTest').classList.remove('hidden');
        document.getElementById('stopTest').classList.add('hidden');
        document.getElementById('stopAllTests').classList.add('hidden'); // Hide stop all button too
    }
    
    async stopAllTests() {
        if (!this.isTestRunning) {
            return;
        }

        try {
            const result = await this.callBridgeAPI('/api/test/stop-all', {
                method: 'POST'
            });

            if (result.success) {
                this.handleTestStopped('All tests stopped by user');
            } else {
                throw new Error(result.error || 'Failed to stop all tests');
            }
        } catch (error) {
            console.error('Stop all tests failed:', error);
            this.handleTestStopped(`Stop all failed: ${error.message}`);
        }
    }

    
    updateProgress(percentage, message) {
        // Fix progress bar jumping by ensuring valid percentage
        const validPercentage = Math.max(0, Math.min(100, percentage));
        
        document.getElementById('progressFill').style.width = `${validPercentage}%`;
        document.getElementById('progressText').textContent = message;
        
        // Store last valid progress to prevent jumping
        this.lastValidProgress = validPercentage;
    }
    
    updateProgressDetails(details) {
        document.getElementById('progressDetails').textContent = details;
    }
    
    updateEnhancedProgress(testInfo) {
        /**
         * Enhanced Progress Update with QLab Metrics and Live Performance Data
         */
        if (!testInfo) return;
        
        const progress = testInfo.progress || 0;
        const elapsedTime = testInfo.elapsed_time || 0;
        const remainingTime = testInfo.remaining_time || 0;
        const liveMetrics = testInfo.live_metrics || {};
        const qlabAnalysis = testInfo.qlab_analysis || {};
        
        // Update main progress bar (fix jumping)
        const validProgress = Math.max(0, Math.min(100, progress));
        if (Math.abs(validProgress - (this.lastValidProgress || 0)) > 0.5) {
            this.updateProgress(validProgress, this.formatProgressMessage(testInfo));
        }
        
        // Update enhanced temperature widget with QLab metrics
        this.updateEnhancedTemperatureWidget(testInfo);
        
        // Update progress details with timing info
        this.updateProgressTiming(elapsedTime, remainingTime, testInfo.estimated_duration);
    }
    
    formatProgressMessage(testInfo) {
        /**
         * Generate informative progress message based on test phase
         */
        const progress = testInfo.progress || 0;
        const qlabAnalysis = testInfo.qlab_analysis || {};
        
        if (progress < 5) {
            return 'Initializing test environment...';
        } else if (progress < 25) {
            return 'Warming up disk - measuring baseline performance...';
        } else if (progress < 75) {
            const status = qlabAnalysis.status_message || 'Running main test...';
            return `Main test phase - ${status}`;
        } else if (progress < 95) {
            return 'Analyzing performance consistency...';
        } else if (progress < 100) {
            return 'Finalizing results...';
        } else {
            return 'Test completed successfully!';
        }
    }
    
    updateEnhancedTemperatureWidget(testInfo) {
        /**
         * Update temperature widget with enhanced QLab performance metrics
         */
        const widget = document.getElementById('temperatureWidget');
        if (!widget || widget.classList.contains('hidden')) return;
        
        const liveMetrics = testInfo.live_metrics || {};
        const qlabAnalysis = testInfo.qlab_analysis || {};
        const elapsedTime = testInfo.elapsed_time || 0;
        const remainingTime = testInfo.remaining_time || 0;
        
        // Create enhanced content if not already exists
        let enhancedContent = widget.querySelector('.enhanced-metrics');
        if (!enhancedContent) {
            enhancedContent = document.createElement('div');
            enhancedContent.className = 'enhanced-metrics';
            widget.appendChild(enhancedContent);
        }
        
        // Format timing display
        const elapsedStr = this.formatDuration(elapsedTime);
        const remainingStr = this.formatDuration(remainingTime);
        const totalStr = this.formatDuration((testInfo.estimated_duration || 0));
        
        // Create enhanced metrics display
        enhancedContent.innerHTML = `
            <div class="metrics-separator"></div>
            
            <div class="progress-section">
                <h4><i class="fas fa-clock"></i> Test Progress</h4>
                <div class="progress-timing">
                    <div class="timing-item">
                        <span class="timing-label">Elapsed:</span>
                        <span class="timing-value">${elapsedStr}</span>
                    </div>
                    <div class="timing-item">
                        <span class="timing-label">Remaining:</span>
                        <span class="timing-value">${remainingStr}</span>
                    </div>
                    <div class="timing-item">
                        <span class="timing-label">Total:</span>
                        <span class="timing-value">${totalStr}</span>
                    </div>
                </div>
            </div>
            
            <div class="metrics-separator"></div>
            
            <div class="performance-section">
                <h4><i class="fas fa-tachometer-alt"></i> Live Performance</h4>
                <div class="performance-grid">
                    <div class="perf-metric">
                        <span class="perf-value">${liveMetrics.throughput_mbps || '--'}</span>
                        <span class="perf-unit">MB/s</span>
                        <span class="perf-label">Current</span>
                    </div>
                    <div class="perf-metric">
                        <span class="perf-value">${liveMetrics.min_throughput_mbps || '--'}</span>
                        <span class="perf-unit">MB/s</span>
                        <span class="perf-label">Minimum</span>
                    </div>
                    <div class="perf-metric">
                        <span class="perf-value">${liveMetrics.iops || '--'}</span>
                        <span class="perf-unit">IOPS</span>
                        <span class="perf-label">Current</span>
                    </div>
                    <div class="perf-metric">
                        <span class="perf-value">${liveMetrics.latency_ms || '--'}</span>
                        <span class="perf-unit">ms</span>
                        <span class="perf-label">Latency</span>
                    </div>
                </div>
            </div>
            
            <div class="metrics-separator"></div>
            
            <div class="qlab-section">
                <h4><i class="fas fa-theater-masks"></i> QLab Reliability</h4>
                <div class="qlab-metrics">
                    <div class="qlab-status ${this.getQLabStatusClass(qlabAnalysis.status)}">
                        ${qlabAnalysis.status_message || 'Analyzing...'}
                    </div>
                    <div class="reliability-grid">
                        <div class="reliability-item">
                            <span class="reliability-label">Stutters:</span>
                            <span class="reliability-value ${this.getReliabilityClass('stutters', liveMetrics.stutters_detected)}">${liveMetrics.stutters_detected || 0}</span>
                        </div>
                        <div class="reliability-item">
                            <span class="reliability-label">Dropouts:</span>
                            <span class="reliability-value ${this.getReliabilityClass('dropouts', liveMetrics.dropouts_detected)}">${liveMetrics.dropouts_detected || 0}</span>
                        </div>
                        <div class="reliability-item">
                            <span class="reliability-label">Consistency:</span>
                            <span class="reliability-value ${this.getReliabilityClass('consistency', qlabAnalysis.consistency_score)}">${qlabAnalysis.consistency_score || '--'}%</span>
                        </div>
                        <div class="reliability-item">
                            <span class="reliability-label">Show Ready:</span>
                            <span class="reliability-value ${qlabAnalysis.show_ready ? 'good' : 'warning'}">${qlabAnalysis.show_ready ? '✅' : '⚠️'}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    formatDuration(seconds) {
        /**
         * Format duration in human-readable format
         */
        if (!seconds || seconds < 0) return '--:--';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}h ${minutes}m`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    }
    
    getQLabStatusClass(status) {
        /**
         * Get CSS class for QLab status
         */
        switch (status) {
            case 'excellent': return 'status-excellent';
            case 'good': return 'status-good';
            case 'fair': return 'status-fair';
            case 'poor': return 'status-poor';
            default: return 'status-unknown';
        }
    }
    
    getReliabilityClass(type, value) {
        /**
         * Get CSS class for reliability metrics
         */
        switch (type) {
            case 'stutters':
                if (value === 0) return 'good';
                if (value <= 2) return 'warning';
                return 'danger';
            case 'dropouts':
                return value === 0 ? 'good' : 'danger';
            case 'consistency':
                if (value >= 95) return 'good';
                if (value >= 85) return 'warning';
                return 'danger';
            default:
                return '';
        }
    }
    
    updateProgressTiming(elapsed, remaining, total) {
        /**
         * Update progress details with timing information
         */
        const progressDetails = document.getElementById('progressDetails');
        if (!progressDetails) return;
        
        const elapsedStr = this.formatDuration(elapsed);
        const remainingStr = this.formatDuration(remaining);
        const totalStr = this.formatDuration(total);
        
        progressDetails.innerHTML = `
            <div class="timing-summary">
                Progress: ${elapsedStr} / ${totalStr} (${remainingStr} remaining)
            </div>
        `;
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
        const baseURL = 'http://localhost:8765';
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
                this.currentTestId = testId; // Store for stopping
            
            // Poll for test completion
            const testResult = await this.pollTestCompletion(testId);
            this.currentTestId = null; // Clear test ID on completion
            return testResult;
            
        } catch (error) {
            console.error('Real test error:', error);
            this.currentTestId = null; // Clear test ID on error
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
                } else if (testInfo.status === 'stopped' || testInfo.status === 'timeout') {
                    // Test was stopped or timed out by the backend
                    this.handleTestStopped(`Test ${testInfo.status} by backend`);
                    throw new Error(`Test ${testInfo.status}`);
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
            // Add timeout and better error handling
            const timeoutPromise = new Promise((_, reject) =>
                setTimeout(() => reject(new Error('Timeout after 10 seconds')), 10000)
            );
            
            const statusPromise = this.callBridgeAPI('/api/status');
            const status = await Promise.race([statusPromise, timeoutPromise]);
            
            if (status && status.success && status.status) {
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
                throw new Error('Invalid response from bridge server');
            }
        } catch (error) {
            console.error('System status check failed:', error);
            this.setupState.systemStatus = 'error';
            this.updateSystemStatus('error', `❌ Status check failed: ${error.message} - <button onclick="app.retryStatusCheck()" style="background: none; border: none; color: inherit; text-decoration: underline; cursor: pointer;">Retry</button>`);
        }
        
        // Always call this to update the setup wizard
        this.updateSetupStep1();
    }
    
    retryStatusCheck() {
        this.checkSystemStatus();
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
        // Reset setup wizard to 1
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
        
        installationProgress.innerHTML = '';
        
        try {
            // Call real setup API
            this.addLogMessage(installationProgress, 'info', 'Starting FIO installation process...');
            
            const setupResult = await this.callBridgeAPI('/api/setup', {
                method: 'POST',
                body: { action: 'install_fio' }
            });
            
            if (setupResult.success) {
                // Show real installation progress
                if (setupResult.logs) {
                    for (const logEntry of setupResult.logs) {
                        this.addLogMessage(installationProgress, logEntry.level || 'info', `[${logEntry.timestamp}] ${logEntry.message}`);
                        await new Promise(resolve => setTimeout(resolve, 200));
                    }
                }
                
                // Refresh system status
                await this.checkSystemStatus();
                
                // Mark step 2 as completed if FIO is now working
                if (this.setupState.fioWorking) {
                    step2.classList.add('completed');
                    step2Status.innerHTML = '<i class="fas fa-check"></i>';
                    this.enableStep3();
                    this.addLogMessage(installationProgress, 'success', 'FIO installation completed successfully!');
                } else {
                    step2Status.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
                    this.addLogMessage(installationProgress, 'warning', 'FIO installation completed but functionality is limited on macOS');
                    this.enableStep3(); // Still enable validation to show current status
                }
                
            } else {
                throw new Error(setupResult.error || 'Installation failed');
            }
            
        } catch (error) {
            console.error('Installation failed:', error);
            this.addLogMessage(installationProgress, 'error', `Installation failed: ${error.message}`);
            step2Status.innerHTML = '<i class="fas fa-times"></i>';
        } finally {
            this.setupState.installationInProgress = false;
            startButton.disabled = false;
        }
    }
    
    async runValidation() {
        const step3 = document.getElementById('step3');
        const step3Status = document.getElementById('step3Status');
        const validationResults = document.getElementById('validationResults');
        const validationButton = document.getElementById('runValidation');
        
        validationButton.disabled = true;
        step3Status.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i>';
        
        validationResults.innerHTML = '';
        
        try {
            // System validation only - temperature monitoring removed
            const result = await this.callBridgeAPI('/api/validate', {
                method: 'POST',
                body: { action: 'run_all_tests' }
            });
            
            let allResults = [];
            if (result.success && result.tests) {
                allResults = result.tests;
            }
            
            const validationResult = {
                success: true,
                tests: allResults
            };
            
            if (validationResult.success && validationResult.tests) {
                // Show real validation results
                for (const test of validationResult.tests) {
                    const testId = `test-${test.name.replace(/\s+/g, '-').toLowerCase()}`;
                    
                    // Add test entry
                    validationResults.innerHTML += `
                        <div class="validation-test" id="${testId}">
                            <span class="validation-test-name">${test.name}</span>
                            <div class="validation-result pending">
                                <i class="fas fa-circle-notch fa-spin"></i> Running...
                            </div>
                        </div>
                    `;
                    
                    // Wait a bit for visual effect
                    await new Promise(resolve => setTimeout(resolve, 500));
                    
                    // Update with real result
                    const testEl = document.getElementById(testId);
                    const resultEl = testEl.querySelector('.validation-result');
                    
                    if (test.passed) {
                        resultEl.innerHTML = `<i class="fas fa-check"></i> ${test.result}`;
                        resultEl.className = 'validation-result pass';
                    } else {
                        resultEl.innerHTML = `<i class="fas fa-times"></i> ${test.result}`;
                        resultEl.className = 'validation-result fail';
                    }
                }
                
                // Update completion status based on overall results
                const allPassed = validationResult.tests.every(test => test.passed);
                
                if (allPassed) {
                    step3.classList.add('completed');
                    step3Status.innerHTML = '<i class="fas fa-check"></i>';
                    this.updateSystemStatus('ready', '✅ System fully validated and ready for testing');
                } else {
                    step3Status.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
                    this.updateSystemStatus('warning', '⚠️ Some validation tests failed - Limited functionality');
                }
                
            } else {
                throw new Error(validationResult.error || 'Validation failed');
            }
            
        } catch (error) {
            console.error('Validation failed:', error);
            validationResults.innerHTML = `
                <div class="validation-test">
                    <span class="validation-test-name">Validation Error</span>
                    <div class="validation-result fail">
                        <i class="fas fa-times"></i> ${error.message}
                    </div>
                </div>
            `;
            step3Status.innerHTML = '<i class="fas fa-times"></i>';
        } finally {
            validationButton.disabled = false;
        }
    }
    
    addLogMessage(container, level, message) {
        const logClass = level === 'error' ? 'error' : level === 'warning' ? 'warning' : level === 'success' ? 'success' : 'info';
        container.innerHTML += `<div class="log-line ${logClass}">[${new Date().toLocaleTimeString()}] ${message}</div>`;
        container.scrollTop = container.scrollHeight;
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
    
    // Pattern Info Modal Functions
    showPatternInfo(patternType) {
        const modal = document.getElementById('patternInfoModal');
        const title = document.getElementById('modalTitle');
        const body = document.getElementById('modalBody');
        
        const patternData = this.getPatternData(patternType);
        
        title.textContent = patternData.title;
        body.innerHTML = patternData.content;
        
        modal.classList.remove('hidden');
        
        // Close modal when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closePatternInfo();
            }
        });
    }
    
    closePatternInfo() {
        const modal = document.getElementById('patternInfoModal');
        modal.classList.add('hidden');
    }
    
    getPatternData(patternType) {
        const patterns = {
            'quick_max_speed': {
                title: 'Quick Max Speed Test - 3 Minutes',
                content: `
                    <div class="pattern-overview">
                        <h4>🚀 Maximum Performance Assessment</h4>
                        <p>Schnelle Ermittlung der maximalen Disk-Performance für erste Einschätzung der System-Fähigkeiten.</p>
                    </div>
                    
                    <div class="pattern-phases">
                        <h4>Test-Phasen (3 Minuten):</h4>
                        <div class="phase-item">
                            <div class="phase-header">
                                <span class="phase-title">Phase 1: Sequential Performance</span>
                                <span class="phase-duration">60s</span>
                            </div>
                            <div class="phase-description">
                                Maximale sequenzielle Read/Write-Performance ermitteln
                            </div>
                        </div>
                        <div class="phase-item">
                            <div class="phase-header">
                                <span class="phase-title">Phase 2: Random Access</span>
                                <span class="phase-duration">60s</span>
                            </div>
                            <div class="phase-description">
                                4K Random Read/Write für Latenz-Assessment
                            </div>
                        </div>
                        <div class="phase-item">
                            <div class="phase-header">
                                <span class="phase-title">Phase 3: Mixed Load</span>
                                <span class="phase-duration">60s</span>
                            </div>
                            <div class="phase-description">
                                Kombinierte Last für realistische Performance-Einschätzung
                            </div>
                        </div>
                    </div>
                    
                    <div class="technical-specs">
                        <h4>Technische Parameter:</h4>
                        <div class="spec-grid">
                            <div class="spec-item">
                                <span class="spec-label">Block Size</span>
                                <span class="spec-value">4K - 1M</span>
                            </div>
                            <div class="spec-item">
                                <span class="spec-label">Queue Depth</span>
                                <span class="spec-value">1 - 32</span>
                            </div>
                            <div class="spec-item">
                                <span class="spec-label">Test Pattern</span>
                                <span class="spec-value">Sequential + Random</span>
                            </div>
                            <div class="spec-item">
                                <span class="spec-label">Ziel-Bandbreite</span>
                                <span class="spec-value">Max. verfügbar</span>
                            </div>
                        </div>
                    </div>
                    
                    <p><strong>Verwendung:</strong> Ideal für schnelle System-Checks und erste Performance-Einschätzung vor längeren Tests.</p>
                `
            },
            'qlab_prores_422_show': {
                title: 'QLab ProRes 422 Show Pattern - 2,75 Stunden',
                content: `
                    <div class="pattern-overview">
                        <h4>🎬 Realistische Show-Simulation</h4>
                        <p>Simuliert eine 2,75-stündige Show mit 1x 4K 50p + 3x HD 50p ProRes 422 Streams inklusive Crossfades alle 3 Minuten.</p>
                    </div>
                    
                    <div class="pattern-phases">
                        <h4>Show-Phasen (2,75 Stunden):</h4>
                        <div class="phase-item">
                            <div class="phase-header">
                                <span class="phase-title">Phase 1: Show-Vorbereitung</span>
                                <span class="phase-duration">30min</span>
                            </div>
                            <div class="phase-description">
                                Moderate Last: ~400 MB/s - Cue-Vorbereitung und System-Check
                            </div>
                        </div>
                        <div class="phase-item">
                            <div class="phase-header">
                                <span class="phase-title">Phase 2: Normale Show-Last</span>
                                <span class="phase-duration">90min</span>
                            </div>
                            <div class="phase-description">
                                Kontinuierliche Last: ~700 MB/s mit Crossfades alle 3min auf 1400 MB/s
                            </div>
                        </div>
                        <div class="phase-item">
                            <div class="phase-header">
                                <span class="phase-title">Phase 3: Show-Finale</span>
                                <span class="phase-duration">75min</span>
                            </div>
                            <div class="phase-description">
                                Intensive Überblendungen: Peaks bis 1400 MB/s, häufige Crossfades
                            </div>
                        </div>
                    </div>
                    
                    <div class="technical-specs">
                        <h4>ProRes 422 Spezifikationen:</h4>
                        <div class="spec-grid">
                            <div class="spec-item">
                                <span class="spec-label">4K 50p Stream</span>
                                <span class="spec-value">~220 MB/s</span>
                            </div>
                            <div class="spec-item">
                                <span class="spec-label">HD 50p Streams (3x)</span>
                                <span class="spec-value">~150 MB/s</span>
                            </div>
                            <div class="spec-item">
                                <span class="spec-label">Crossfade Peaks</span>
                                <span class="spec-value">700→1400 MB/s</span>
                            </div>
                            <div class="spec-item">
                                <span class="spec-label">Crossfade Interval</span>
                                <span class="spec-value">Alle 3 Minuten</span>
                            </div>
                        </div>
                    </div>
                    
                    <p><strong>Thermal Testing:</strong> Überwacht Performance-Degradation über 2,75h und bewertet Show-Tauglichkeit.</p>
                `
            },
            'qlab_prores_hq_show': {
                title: 'QLab ProRes HQ Show Pattern - 2,75 Stunden',
                content: `
                    <div class="pattern-overview">
                        <h4>🎬 High-Quality Show-Simulation</h4>
                        <p>Simuliert eine 2,75-stündige Show mit 1x 4K 50p + 3x HD 50p ProRes HQ Streams - höchste Qualitätsanforderungen.</p>
                    </div>
                    
                    <div class="pattern-phases">
                        <h4>Show-Phasen (2,75 Stunden):</h4>
                        <div class="phase-item">
                            <div class="phase-header">
                                <span class="phase-title">Phase 1: Show-Vorbereitung</span>
                                <span class="phase-duration">30min</span>
                            </div>
                            <div class="phase-description">
                                HQ-Vorbereitung: ~800 MB/s - Intensive Cue-Checks
                            </div>
                        </div>
                        <div class="phase-item">
                            <div class="phase-header">
                                <span class="phase-title">Phase 2: Normale Show-Last</span>
                                <span class="phase-duration">90min</span>
                            </div>
                            <div class="phase-description">
                                Kontinuierliche HQ-Last: ~1400 MB/s mit Crossfades alle 3min auf 2800 MB/s
                            </div>
                        </div>
                        <div class="phase-item">
                            <div class="phase-header">
                                <span class="phase-title">Phase 3: Show-Finale</span>
                                <span class="phase-duration">75min</span>
                            </div>
                            <div class="phase-description">
                                Maximale HQ-Überblendungen: Peaks bis 2800 MB/s, intensive Crossfades
                            </div>
                        </div>
                    </div>
                    
                    <div class="technical-specs">
                        <h4>ProRes HQ Spezifikationen:</h4>
                        <div class="spec-grid">
                            <div class="spec-item">
                                <span class="spec-label">4K 50p Stream</span>
                                <span class="spec-value">~440 MB/s</span>
                            </div>
                            <div class="spec-item">
                                <span class="spec-label">HD 50p Streams (3x)</span>
                                <span class="spec-value">~300 MB/s</span>
                            </div>
                            <div class="spec-item">
                                <span class="spec-label">Crossfade Peaks</span>
                                <span class="spec-value">1400→2800 MB/s</span>
                            </div>
                            <div class="spec-item">
                                <span class="spec-label">Thermal Stress</span>
                                <span class="spec-value">Sehr hoch</span>
                            </div>
                        </div>
                    </div>
                    
                    <p><strong>Professional Grade:</strong> Höchste Anforderungen - nur für High-End-SSDs empfohlen.</p>
                `
            },
            'max_sustained': {
                title: 'Maximum Sustained Performance - 1,5 Stunden',
                content: `
                    <div class="pattern-overview">
                        <h4>🔥 Thermal Stress Testing</h4>
                        <p>Kontinuierliche Maximallast über 1,5 Stunden zur Bewertung der thermischen Stabilität und Performance-Retention.</p>
                    </div>
                    
                    <div class="pattern-phases">
                        <h4>Thermal Test-Phasen (1,5 Stunden):</h4>
                        <div class="phase-item">
                            <div class="phase-header">
                                <span class="phase-title">Phase 1: Aufwärmung</span>
                                <span class="phase-duration">15min</span>
                            </div>
                            <div class="phase-description">
                                Graduelle Steigerung zur Maximallast - Thermal Baseline
                            </div>
                        </div>
                        <div class="phase-item">
                            <div class="phase-header">
                                <span class="phase-title">Phase 2: Sustained Maximum</span>
                                <span class="phase-duration">60min</span>
                            </div>
                            <div class="phase-description">
                                Kontinuierliche Maximallast - Throttling-Detektion
                            </div>
                        </div>
                        <div class="phase-item">
                            <div class="phase-header">
                                <span class="phase-title">Phase 3: Stress Burst</span>
                                <span class="phase-duration">15min</span>
                            </div>
                            <div class="phase-description">
                                Burst-Pattern mit Peaks - Worst-Case-Szenario
                            </div>
                        </div>
                    </div>
                    
                    <div class="technical-specs">
                        <h4>Thermal Testing Parameter:</h4>
                        <div class="spec-grid">
                            <div class="spec-item">
                                <span class="spec-label">Test-Pattern</span>
                                <span class="spec-value">Sequential + Random + Mixed</span>
                            </div>
                            <div class="spec-item">
                                <span class="spec-label">Load Level</span>
                                <span class="spec-value">100% Maximum</span>
                            </div>
                            <div class="spec-item">
                                <span class="spec-label">Throttling Check</span>
                                <span class="spec-value">30min Intervalle</span>
                            </div>
                            <div class="spec-item">
                                <span class="spec-label">Performance Retention</span>
                                <span class="spec-value">Kontinuierlich</span>
                            </div>
                        </div>
                    </div>
                    
                    <p><strong>Bewertung:</strong> Klassifiziert SSDs als "Professional Grade", "Consumer Grade" oder "Limited Use" basierend auf thermischer Performance.</p>
                `
            }
        };
        
        return patterns[patternType] || {
            title: 'Unknown Test Pattern',
            content: '<p>Pattern information not available.</p>'
        };
    }
    
}

// Global functions for modal (called from HTML onclick)
function showPatternInfo(patternType) {
    if (window.app) {
        window.app.showPatternInfo(patternType);
    }
}

function closePatternInfo() {
    if (window.app) {
        window.app.closePatternInfo();
    }
}

// Initialize the application when the page loads
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new DiskBenchApp();
    // Make app globally available for modal functions
    window.app = app;
});


