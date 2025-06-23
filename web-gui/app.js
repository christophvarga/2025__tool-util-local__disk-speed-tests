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
        this.currentTestDuration = 0; // To store the duration of the current test
        
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
        this.checkForActiveTest();
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
    
    async startTest() {
        if (!this.selectedDisk || this.isTestRunning) {
            return;
        }
        
        this.isTestRunning = true;
        this.testResults = null;
        this.currentTestDuration = 0; // Reset duration at the start of a new test
        
        // Show progress section
        document.getElementById('progressSection').classList.remove('hidden');
        document.getElementById('resultsSection').classList.add('hidden');
        document.getElementById('startTest').classList.add('hidden');
        document.getElementById('stopTest').classList.remove('hidden');
        document.getElementById('stopAllTests').classList.add('hidden'); // keep hidden for single-test mode
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
            
            // Execute test (this only starts the test, doesn't wait for completion)
            const result = await this.executeDiskBenchCommand(command);
            
            if (result && result.success) {
                // Test started successfully - polling will handle the rest
                this.updateProgress(5, 'Test started successfully...');
                this.updateProgressDetails('Test is now running in background. Polling for updates...');
            } else {
                throw new Error('Failed to start test - no confirmation received');
            }
            
        } catch (error) {
            console.error('Test failed:', error);
            this.updateProgress(0, `Test failed: ${error.message}`);
            this.updateProgressDetails(`Error: ${error.message}`);
            
            // Only reset state on error
            this.isTestRunning = false;
            this.currentTestId = null;
            this.updateUI();
            document.getElementById('startTest').classList.remove('hidden');
            document.getElementById('stopTest').classList.add('hidden');
            document.getElementById('stopAllTests').classList.add('hidden');
        }
        // Note: No finally block - let polling handle successful completion
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
        const estimatedDuration = testInfo.estimated_duration || this.currentTestDuration;
        
        if (testInfo.estimated_duration) {
            this.currentTestDuration = testInfo.estimated_duration;
        }
        
        // Fix duration calculations - ensure we have valid numbers
        const validElapsed = Math.max(0, elapsedTime);
        const validRemaining = Math.max(0, remainingTime);
        const validEstimated = Math.max(0, estimatedDuration);
        
        // Update main progress bar with enhanced phase information
        const validProgress = Math.max(0, Math.min(100, progress));
        if (Math.abs(validProgress - (this.lastValidProgress || 0)) > 0.5) {
            // Use the enhanced test phase name from backend
            const phaseMessage = testInfo.test_phase_name || `Test running... ${validProgress.toFixed(1)}%`;
            this.updateProgress(validProgress, phaseMessage);
        }
        
        // Update progress details with timing info
        this.updateProgressTiming(validElapsed, validRemaining, validEstimated);
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
    
    showResults(results) {
        document.getElementById('resultsSection').classList.remove('hidden');
        document.getElementById('exportResults').classList.remove('hidden');
        
        // Determine which analyzer to use based on test type
        const testType = this.selectedTestType;
        
        console.log('showResults called with testType:', testType);
        console.log('Results data:', results);
        
        if (testType === 'quick_max_speed') {
            console.log('Rendering Test 1 Analysis');
            this.renderTest1Analysis(results);
        } else if (testType === 'qlab_prores_422_show') {
            console.log('Rendering Test 2 Analysis');
            this.renderTest2Analysis(results);
        } else if (testType === 'qlab_prores_hq_show') {
            console.log('Rendering Test 3 Analysis');
            this.renderTest3Analysis(results);
        } else if (testType === 'max_sustained') {
            console.log('Rendering Test 4 Analysis');
            this.renderTest4Analysis(results);
        } else {
            console.log('Rendering Generic Analysis for unknown test type:', testType);
            // Fallback to generic analysis
            this.renderGenericAnalysis(results);
        }
        
        // Always render implementation details
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
    
    // ===== TEST-SPECIFIC ANALYZERS =====
    
    renderTest1Analysis(results) {
        /**
         * Test 1: Quick Setup & Performance Check (1 minute)
         * Focus: Basic disk performance assessment and system check
         */
        const container = document.getElementById('qlabAnalysis');
        const analysis = results.qlab_analysis || results.analysis || {};
        const summary = results.fio_results?.summary || {};
        
        // Clear the detailed metrics container to prevent generic metrics from showing
        document.getElementById('detailedMetrics').innerHTML = '';
        
        // Extract key metrics
        const readBW = (summary.total_read_bw || 0) / 1024; // Convert to MB/s
        const writeBW = (summary.total_write_bw || 0) / 1024;
        const readIOPS = summary.total_read_iops || 0;
        const avgLatency = summary.avg_read_latency || 0;
        
        // Basic performance classification (NOT QLab-specific)
        let performanceClass, classColor, description;
        if (readBW > 2000) {
            performanceClass = 'HIGH-END SSD';
            classColor = 'excellent';
            description = 'Excellent disk performance detected';
        } else if (readBW > 1000) {
            performanceClass = 'GOOD SSD';
            classColor = 'good';
            description = 'Good disk performance detected';
        } else if (readBW > 500) {
            performanceClass = 'STANDARD SSD';
            classColor = 'warning';
            description = 'Standard disk performance detected';
        } else if (readBW > 100) {
            performanceClass = 'BASIC DISK';
            classColor = 'warning';
            description = 'Basic disk performance detected';
        } else {
            performanceClass = 'SLOW DISK';
            classColor = 'danger';
            description = 'Limited disk performance detected';
        }
        
        container.innerHTML = `
            <div class="test-analysis-header">
                <h3>📊 Test 1: Quick Setup & Performance Check</h3>
                <div class="test-load-info">
                    <strong>Test Duration:</strong> 1 minute quick assessment<br>
                    <strong>Purpose:</strong> Basic disk performance check and system validation<br>
                    <strong>Note:</strong> This is NOT a QLab-specific test
                </div>
                <div class="tier-badge ${classColor}">⚡ ${performanceClass}</div>
            </div>
            
            <div class="basic-metrics">
                <h4>📈 Basic Performance Metrics</h4>
                <div class="metrics-grid">
                    <div class="metric-item">
                        <div class="metric-label">Sequential Read</div>
                        <div class="metric-value">${readBW.toFixed(0)} MB/s</div>
                        <div class="metric-status">Peak performance</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Sequential Write</div>
                        <div class="metric-value">${writeBW.toFixed(0)} MB/s</div>
                        <div class="metric-status">Peak performance</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Random Access</div>
                        <div class="metric-value">${this.formatNumber(readIOPS)}</div>
                        <div class="metric-status">IOPS capability</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Response Time</div>
                        <div class="metric-value">${avgLatency.toFixed(1)} ms</div>
                        <div class="metric-status">Average latency</div>
                    </div>
                </div>
            </div>
            
            <div class="system-assessment">
                <h4>🔧 System Assessment</h4>
                <div class="assessment-summary ${classColor}">
                    <div class="assessment-result">${description}</div>
                    <div class="assessment-note">
                        This quick test provides a basic performance overview. 
                        For QLab-specific analysis, run Test 2 or Test 3.
                    </div>
                </div>
            </div>
            
            <div class="next-steps">
                <h4>➡️ Next Steps</h4>
                <div class="recommendation-list">
                    <div class="recommendation-item">
                        📋 <strong>System Check Complete:</strong> Basic disk performance measured
                    </div>
                    <div class="recommendation-item">
                        🎬 <strong>For QLab Analysis:</strong> Run Test 2 (ProRes 422) or Test 3 (ProRes HQ)
                    </div>
                    <div class="recommendation-item">
                        ⚡ <strong>For Sustained Performance:</strong> Run Test 4 (Max Sustained)
                    </div>
                    <div class="recommendation-item">
                        💡 <strong>Performance Class:</strong> ${performanceClass} - ${description.toLowerCase()}
                    </div>
                </div>
            </div>
        `;
    }
    
    generateTest1Recommendations(readBW, latency, tier) {
        const recommendations = [];
        
        if (tier === 'FLAGSHIP') {
            recommendations.push('🏆 Excellent for any QLab production including complex ProRes HQ workflows');
            recommendations.push('🎯 Run Test 2 & 3 to confirm sustained performance for long shows');
        } else if (tier === 'PROFESSIONAL') {
            recommendations.push('🥇 Great for ProRes 422 production workflows');
            recommendations.push('🎯 Test ProRes HQ scenarios with Test 3 before critical shows');
        } else if (tier === 'STANDARD') {
            recommendations.push('🥈 Suitable for HD and conservative 4K workflows');
            recommendations.push('⚠️ Avoid complex crossfades and multiple simultaneous streams');
        } else if (tier === 'BASIC') {
            recommendations.push('🥉 Limited to HD production only');
            recommendations.push('💡 Consider SSD upgrade for 4K workflows');
        } else {
            recommendations.push('❌ Not suitable for professional QLab production');
            recommendations.push('🔧 Storage upgrade required');
        }
        
        if (latency > 10) {
            recommendations.push('⚠️ High latency detected - may affect cue triggering responsiveness');
        }
        
        recommendations.push('📈 Next: Run Test 2 (ProRes 422 Show) for realistic show simulation');
        
        return recommendations.map(rec => `<div class="recommendation-item">${rec}</div>`).join('');
    }
    
    generateQLabRecommendations(readBW, avgLatency, tier) {
        const recommendations = [];
        
        if (tier === 'FLAGSHIP') {
            recommendations.push('<li>🏆 Excellent for complex QLab productions with multiple ProRes streams</li>');
            recommendations.push('<li>✅ Suitable for demanding crossfades and simultaneous playback</li>');
            recommendations.push('<li>🎯 Perfect for professional theater and concert productions</li>');
        } else if (tier === 'PROFESSIONAL') {
            recommendations.push('<li>🥇 Great for standard QLab productions</li>');
            recommendations.push('<li>✅ Handles most ProRes workflows reliably</li>');
            recommendations.push('<li>⚠️ Test complex scenarios before critical shows</li>');
        } else if (tier === 'STANDARD') {
            recommendations.push('<li>🥈 Suitable for basic QLab workflows</li>');
            recommendations.push('<li>⚠️ Avoid complex crossfades and multiple streams</li>');
            recommendations.push('<li>💡 Consider limiting to HD content for reliability</li>');
        } else {
            recommendations.push('<li>❌ Not recommended for professional QLab use</li>');
            recommendations.push('<li>🔧 Storage upgrade strongly recommended</li>');
            recommendations.push('<li>⚠️ May experience dropouts and performance issues</li>');
        }
        
        if (avgLatency > 10) {
            recommendations.push('<li>⚠️ High latency may affect cue triggering responsiveness</li>');
        }
        
        if (readBW < 100) {
            recommendations.push('<li>🚨 Very low bandwidth - unsuitable for video playback</li>');
        }
        
        return recommendations.join('');
    }
    
    renderTest2Analysis(results) {
        /**
         * Test 2: ProRes 422 Production Test (2.5 hours, multi-phase)
         * Focus: Realistic show simulation with thermal stability assessment
         */
        const container = document.getElementById('qlabAnalysis');
        const analysis = results.qlab_analysis || results.analysis || {};
        const summary = results.fio_results?.summary || {};
        
        // Clear the detailed metrics container to prevent generic metrics from showing
        document.getElementById('detailedMetrics').innerHTML = '';
        
        // Extract key metrics from multi-phase test
        const readBW = (summary.total_read_bw || 0) / 1024;
        const minBW = (summary.min_read_bw || readBW) / 1024;
        const maxBW = (summary.max_read_bw || readBW) / 1024;
        const avgLatency = summary.avg_read_latency || 0;
        
        // QLab ProRes 422 Requirements
        const requiredBW = 220; // MB/s for ProRes 422
        const performanceTier = this.getQLabPerformanceTier(readBW, requiredBW);
        
        container.innerHTML = `
            <div class="test-analysis-header">
                <h3>🎬 Test 2: ProRes 422 Show Simulation</h3>
                <div class="test-load-info">
                    <strong>Test Duration:</strong> ~2.5 hours (multi-phase)<br>
                    <strong>Purpose:</strong> Simulate realistic show conditions and assess thermal stability
                </div>
                <div class="tier-badge ${performanceTier.class}">${performanceTier.message}</div>
            </div>
            
            <div class="qlab-metrics">
                <h4>📊 QLab Performance Metrics</h4>
                <div class="metrics-grid">
                    <div class="metric-item">
                        <div class="metric-label">Average Read Speed</div>
                        <div class="metric-value">${readBW.toFixed(0)} MB/s</div>
                        <div class="metric-status">Overall average</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Min Read Speed</div>
                        <div class="metric-value">${minBW.toFixed(0)} MB/s</div>
                        <div class="metric-status">Lowest sustained speed</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Max Read Speed</div>
                        <div class="metric-value">${maxBW.toFixed(0)} MB/s</div>
                        <div class="metric-status">Peak speed during test</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Average Latency</div>
                        <div class="metric-value">${avgLatency.toFixed(1)} ms</div>
                        <div class="metric-status">Cue response time</div>
                    </div>
                </div>
            </div>
            
            <div class="qlab-analysis">
                <h4>💡 QLab Performance Analysis</h4>
                <div class="analysis-grid">
                    <div class="analysis-section">
                        <h5>Performance Tier</h5>
                        <ul>
                            <li>${performanceTier.message}</li>
                        </ul>
                    </div>
                    <div class="analysis-section">
                        <h5>Recommendations</h5>
                        <ul>
                            ${this.generateQLabRecommendations(readBW, avgLatency, performanceTier.tier)}
                        </ul>
                    </div>
                </div>
            </div>
        `;
    }
    
    getQLabPerformanceTier(currentBW, requiredBW) {
        let tier, message, tierClass;
        
        if (currentBW >= requiredBW * 1.2) { // 20% buffer
            tier = 'FLAGSHIP';
            message = '✅ Excellent for QLab (ProRes 422)';
            tierClass = 'excellent';
        } else if (currentBW >= requiredBW * 1.05) { // 5% buffer
            tier = 'PROFESSIONAL';
            message = '✅ Good for QLab (ProRes 422)';
            tierClass = 'good';
        } else if (currentBW >= requiredBW) {
            tier = 'STANDARD';
            message = '⚠️ Fair for QLab (ProRes 422)';
            tierClass = 'warning';
        } else {
            tier = 'BASIC';
            message = '❌ Poor for QLab (ProRes 422)';
            tierClass = 'danger';
        }
        
        return { tier, message, class: tierClass };
    }
    
    renderTest3Analysis(results) {
        /**
         * Test 3: ProRes HQ Production Test (2.5 hours, multi-phase)
         * Focus: High-demand show simulation, critical for 4K ProRes HQ
         */
        const container = document.getElementById('qlabAnalysis');
        const analysis = results.qlab_analysis || results.analysis || {};
        const summary = results.fio_results?.summary || {};
        
        // Clear the detailed metrics container to prevent generic metrics from showing
        document.getElementById('detailedMetrics').innerHTML = '';
        
        // Extract key metrics
        const readBW = (summary.total_read_bw || 0) / 1024;
        const minBW = (summary.min_read_bw || readBW) / 1024;
        const maxBW = (summary.max_read_bw || readBW) / 1024;
        const avgLatency = summary.avg_read_latency || 0;
        
        // QLab ProRes HQ Requirements
        const requiredBW = 440; // MB/s for ProRes HQ
        const performanceTier = this.getQLabPerformanceTier(readBW, requiredBW);
        
        container.innerHTML = `
            <div class="test-analysis-header">
                <h3>🎬 Test 3: ProRes HQ Show Simulation</h3>
                <div class="test-load-info">
                    <strong>Test Duration:</strong> ~2.5 hours (multi-phase)<br>
                    <strong>Purpose:</strong> Simulate high-demand 4K ProRes HQ show conditions
                </div>
                <div class="tier-badge ${performanceTier.class}">${performanceTier.message}</div>
            </div>
            
            <div class="qlab-metrics">
                <h4>📊 QLab Performance Metrics</h4>
                <div class="metrics-grid">
                    <div class="metric-item">
                        <div class="metric-label">Average Read Speed</div>
                        <div class="metric-value">${readBW.toFixed(0)} MB/s</div>
                        <div class="metric-status">Overall average</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Min Read Speed</div>
                        <div class="metric-value">${minBW.toFixed(0)} MB/s</div>
                        <div class="metric-status">Lowest sustained speed</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Max Read Speed</div>
                        <div class="metric-value">${maxBW.toFixed(0)} MB/s</div>
                        <div class="metric-status">Peak speed during test</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Average Latency</div>
                        <div class="metric-value">${avgLatency.toFixed(1)} ms</div>
                        <div class="metric-status">Cue response time</div>
                    </div>
                </div>
            </div>
            
            <div class="qlab-analysis">
                <h4>💡 QLab Performance Analysis</h4>
                <div class="analysis-grid">
                    <div class="analysis-section">
                        <h5>Performance Tier</h5>
                        <ul>
                            <li>${performanceTier.message}</li>
                        </ul>
                    </div>
                    <div class="analysis-section">
                        <h5>Recommendations</h5>
                        <ul>
                            ${this.generateQLabRecommendations(readBW, avgLatency, performanceTier.tier)}
                        </ul>
                    </div>
                </div>
            </div>
        `;
    }
    
    renderTest4Analysis(results) {
        /**
         * Test 4: Max Sustained Performance (1.5 hours)
         * Focus: Long-term stability and thermal throttling assessment
         */
        const container = document.getElementById('qlabAnalysis');
        const analysis = results.qlab_analysis || results.analysis || {};
        const summary = results.fio_results?.summary || {};
        
        // Clear the detailed metrics container to prevent generic metrics from showing
        document.getElementById('detailedMetrics').innerHTML = '';
        
        // Extract key metrics
        const readBW = (summary.total_read_bw || 0) / 1024;
        const minBW = (summary.min_read_bw || readBW) / 1024;
        const maxBW = (summary.max_read_bw || readBW) / 1024;
        const avgLatency = summary.avg_read_latency || 0;
        
        // QLab Sustained Performance Requirements
        const requiredBW = 300; // MB/s for sustained performance
        const performanceTier = this.getQLabPerformanceTier(readBW, requiredBW);
        
        container.innerHTML = `
            <div class="test-analysis-header">
                <h3>🔥 Test 4: Max Sustained Performance</h3>
                <div class="test-load-info">
                    <strong>Test Duration:</strong> ~1.5 hours<br>
                    <strong>Purpose:</strong> Assess long-term stability and thermal throttling
                </div>
                <div class="tier-badge ${performanceTier.class}">${performanceTier.message}</div>
            </div>
            
            <div class="qlab-metrics">
                <h4>📊 Sustained Performance Metrics</h4>
                <div class="metrics-grid">
                    <div class="metric-item">
                        <div class="metric-label">Average Read Speed</div>
                        <div class="metric-value">${readBW.toFixed(0)} MB/s</div>
                        <div class="metric-status">Overall average</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Min Read Speed</div>
                        <div class="metric-value">${minBW.toFixed(0)} MB/s</div>
                        <div class="metric-status">Lowest sustained speed</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Max Read Speed</div>
                        <div class="metric-value">${maxBW.toFixed(0)} MB/s</div>
                        <div class="metric-status">Peak speed during test</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Average Latency</div>
                        <div class="metric-value">${avgLatency.toFixed(1)} ms</div>
                        <div class="metric-status">Cue response time</div>
                    </div>
                </div>
            </div>
            
            <div class="qlab-analysis">
                <h4>💡 Performance Analysis</h4>
                <div class="analysis-grid">
                    <div class="analysis-section">
                        <h5>Performance Tier</h5>
                        <ul>
                            <li>${performanceTier.message}</li>
                        </ul>
                    </div>
                    <div class="analysis-section">
                        <h5>Recommendations</h5>
                        <ul>
                            ${this.generateQLabRecommendations(readBW, avgLatency, performanceTier.tier)}
                        </ul>
                    </div>
                </div>
            </div>
        `;
    }
    
    renderGenericAnalysis(results) {
        /**
         * Fallback for unknown test types
         */
        const container = document.getElementById('qlabAnalysis');
        const summary = results.fio_results?.summary || {};
        
        // Clear the detailed metrics container to prevent generic metrics from showing
        document.getElementById('detailedMetrics').innerHTML = '';
        
        const readBW = (summary.total_read_bw || 0) / 1024;
        const avgLatency = summary.avg_read_latency || 0;
        
        container.innerHTML = `
            <div class="test-analysis-header">
                <h3>❓ Unknown Test Type Analysis</h3>
                <div class="test-load-info">
                    <strong>Test Type:</strong> ${this.selectedTestType}<br>
                    <strong>Purpose:</strong> Generic performance assessment
                </div>
            </div>
            
            <div class="basic-metrics">
                <h4>📈 Basic Performance Metrics</h4>
                <div class="metrics-grid">
                    <div class="metric-item">
                        <div class="metric-label">Sequential Read</div>
                        <div class="metric-value">${readBW.toFixed(0)} MB/s</div>
                        <div class="metric-status">Overall average</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Average Latency</div>
                        <div class="metric-value">${avgLatency.toFixed(1)} ms</div>
                        <div class="metric-status">Average latency</div>
                    </div>
                </div>
            </div>
            
            <div class="next-steps">
                <h4>➡️ Next Steps</h4>
                <div class="recommendation-list">
                    <div class="recommendation-item">
                        ❓ Unknown test type. Please select a known test.
                    </div>
                </div>
            </div>
        `;
    }
    
    // ===== SETUP WIZARD LOGIC =====
    
    async checkSystemStatus() {
        this.setupState.systemStatus = 'checking';
        this.updateSetupUI();
        
        try {
            const result = await this.callBridgeAPI('/api/status');
            
            if (result.success) {
                this.setupState.fioAvailable = result.fio_available || false;
                this.setupState.fioWorking = result.fio_working || false;
                this.setupState.diskAccess = result.disk_access || false;
                this.setupState.systemStatus = 'checked';
                
                // If FIO is not working, prompt for installation
                if (!this.setupState.fioWorking) {
                    this.setupState.setupStep = 2; // Move to installation step
                } else {
                    this.setupState.setupStep = 3; // Skip installation if FIO is fine
                }
            } else {
                throw new Error(result.error || 'Failed to get system status');
            }
        } catch (error) {
            console.error('Error checking system status:', error);
            this.setupState.systemStatus = 'error';
            this.setupState.setupStep = 1; // Go back to initial check
        } finally {
            this.updateSetupUI();
        }
    }
    
    async startInstallation() {
        this.setupState.installationInProgress = true;
        this.setupState.setupStep = 2; // Move to installation step
        this.updateSetupUI();
        
        try {
            const result = await this.callBridgeAPI('/api/setup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'install_fio' })
            });
            
            if (result.success) {
                // Installation successful, re-check status
                await this.checkSystemStatus();
                this.setupState.setupStep = 3; // Move to validation step
            } else {
                throw new Error(result.error || 'Installation failed');
            }
        } catch (error) {
            console.error('Installation error:', error);
            this.setupState.setupStep = 2; // Stay on installation step
            this.showSetupError(`Installation failed: ${error.message}`);
        } finally {
            this.setupState.installationInProgress = false;
            this.updateSetupUI();
        }
    }
    
    async runValidation() {
        this.setupState.setupStep = 3; // Move to validation step
        this.updateSetupUI();
        
        try {
            const result = await this.callBridgeAPI('/api/validate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'run_all_tests' })
            });
            
            if (result.success && result.overall_status === 'passed') {
                this.setupState.setupStep = 4; // All checks passed
            } else if (result.success && result.overall_status === 'failed') {
                this.setupState.setupStep = 3; // Validation failed, stay on this step
                this.showSetupError(`Validation failed: ${result.tests.filter(t => !t.passed).map(t => t.name).join(', ')}`);
            } else {
                throw new Error(result.error || 'Validation process failed');
            }
        } catch (error) {
            console.error('Validation error:', error);
            this.setupState.setupStep = 3; // Stay on validation step
            this.showSetupError(`Validation error: ${error.message}`);
        } finally {
            this.updateSetupUI();
        }
    }
    
    closeSetup() {
        // Hide setup section and show testing section
        document.getElementById('setupWizard').classList.add('hidden');
        document.getElementById('testingSection').classList.remove('hidden');
        this.currentTab = 'testing';
    }
    
    skipSetup() {
        // Mark setup as complete and hide it
        this.setupState.setupStep = 4; // Mark as complete
        this.updateSetupUI();
        this.closeSetup();
    }
    
    retrySetup() {
        // Reset setup state to re-run checks
        this.setupState = {
            systemStatus: 'checking',
            fioAvailable: false,
            fioWorking: false,
            diskAccess: false,
            setupStep: 1,
            installationInProgress: false
        };
        this.checkSystemStatus(); // Re-run the initial check
        this.updateSetupUI();
    }
    
    updateSetupUI() {
        const setupWizard = document.getElementById('setupWizard');
        const testingSection = document.getElementById('testingSection');
        
        // Show/hide sections based on current tab
        if (this.currentTab === 'setup') {
            setupWizard.classList.remove('hidden');
            testingSection.classList.add('hidden');
        } else {
            setupWizard.classList.add('hidden');
            testingSection.classList.remove('hidden');
        }
        
        // Update step indicators
        document.getElementById('step1Indicator').classList.toggle('active', this.setupState.setupStep >= 1);
        document.getElementById('step2Indicator').classList.toggle('active', this.setupState.setupStep >= 2);
        document.getElementById('step3Indicator').classList.toggle('active', this.setupState.setupStep >= 3);
        document.getElementById('step4Indicator').classList.toggle('active', this.setupState.setupStep >= 4);
        
        // Update status messages and controls
        const statusMessage = document.getElementById('statusMessage');
        const fioStatus = document.getElementById('fioStatus');
        const diskStatus = document.getElementById('diskStatus');
        const installButton = document.getElementById('startInstallation');
        const validationButton = document.getElementById('runValidation');
        const closeButton = document.getElementById('closeSetup');
        const skipButton = document.getElementById('skipSetup');
        const retryButton = document.getElementById('retrySetup');
        
        // Status messages
        statusMessage.textContent = this.getSetupStatusMessage();
        fioStatus.textContent = this.getFIOStatus();
        diskStatus.textContent = this.getDiskAccessStatus();
        
        // Button states
        installButton.disabled = this.setupState.installationInProgress || this.setupState.setupStep >= 2;
        validationButton.disabled = this.setupState.installationInProgress || this.setupState.setupStep < 3 || this.setupState.setupStep >= 4;
        closeButton.disabled = this.setupState.setupStep < 4;
        skipButton.disabled = this.setupState.setupStep >= 4;
        retryButton.disabled = this.setupState.installationInProgress;
        
        // Show/hide installation progress
        document.getElementById('installationProgress').classList.toggle('hidden', !this.setupState.installationInProgress);
        
        // Show/hide completion message
        document.getElementById('setupCompleteMessage').classList.toggle('hidden', this.setupState.setupStep < 4);
    }
    
    getSetupStatusMessage() {
        if (this.setupState.systemStatus === 'checking') return 'Checking system status...';
        if (this.setupState.systemStatus === 'error') return 'Error checking system status.';
        if (this.setupState.setupStep === 4) return 'System setup complete!';
        return 'System status checked.';
    }
    
    getFIOStatus() {
        if (this.setupState.fioAvailable) {
            if (this.setupState.fioWorking) return '✅ FIO is installed and working correctly.';
            else return '⚠️ FIO is installed but has issues (shared memory).';
        } else {
            return '❌ FIO is not installed or not found.';
        }
    }
    
    getDiskAccessStatus() {
        if (this.setupState.diskAccess) return '✅ Disk access is permitted.';
        else return '❌ Disk access denied or unavailable.';
    }
    
    showSetupError(message) {
        const errorElement = document.getElementById('setupErrorMessage');
        errorElement.textContent = message;
        errorElement.classList.remove('hidden');
    }
    
    // ===== API CALLS =====
    
    async callBridgeAPI(endpoint, options = {}) {
        const baseUrl = 'http://localhost:8765'; // Bridge server address
        const url = baseUrl + endpoint;
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        };
        
        const mergedOptions = { ...defaultOptions, ...options };
        
        // Add default method POST if not provided and body exists
        if (mergedOptions.body && !mergedOptions.method) {
            mergedOptions.method = 'POST';
        }
        
        try {
            const response = await fetch(url, mergedOptions);
            
            if (!response.ok) {
                let errorMsg = `HTTP error! status: ${response.status}`;
                try {
                    const errorData = await response.json();
                    errorMsg = errorData.error || errorMsg;
                } catch (e) { /* ignore if response is not JSON */ }
                throw new Error(errorMsg);
            }
            
            return await response.json();
            
        } catch (error) {
            console.error(`API call failed for ${url}:`, error);
            throw error; // Re-throw to be caught by caller
        }
    }
    
    async executeDiskBenchCommand(args) {
        // This function is a placeholder for direct execution if needed,
        // but we primarily use the bridge API.
        // For now, we'll simulate a call to the bridge API that wraps diskbench.
        
        // If the command is '--list-disks', call the bridge's list_disks endpoint
        if (args[0] === '--list-disks' && args[1] === '--json') {
            const result = await this.callBridgeAPI('/api/disks');
            return result;
        }
        
        // If the command is '--test', we need to start a test via the bridge
        if (args[0] === '--test') {
            const testType = args[1];
            const diskPath = args[3];
            const size = parseInt(args[5]);
            const outputFile = args[7]; // Output file is passed directly
            const showProgress = args.includes('--progress');
            
            const testParams = {
                test_type: testType,
                disk_path: diskPath,
                size_gb: size,
                output_file: outputFile,
                show_progress: showProgress
            };
            
            // Start the test via the bridge API
            const startResult = await this.callBridgeAPI('/api/test/start', {
                method: 'POST',
                body: JSON.stringify(testParams)
            });
            
            if (startResult.success) {
                this.currentTestId = startResult.test_id; // Store the test ID
                this.currentTestDuration = startResult.estimated_duration || 0; // Store estimated duration
                
                // Poll for test status updates
                this.pollTestStatus(this.currentTestId);
                
                // Return a mock result structure that includes test_info
                // The actual results will be fetched via polling
                return {
                    success: true,
                    test_info: {
                        test_id: this.currentTestId,
                        status: 'started',
                        disk_path: diskPath,
                        test_type: testType,
                        estimated_duration: this.currentTestDuration
                    }
                };
            } else {
                throw new Error(startResult.error || 'Failed to start test');
            }
        }
        
        // Handle other commands if necessary (e.g., --version, --validate)
        if (args[0] === '--version') {
            return await this.callBridgeAPI('/api/version');
        }
        if (args[0] === '--validate') {
            return await this.callBridgeAPI('/api/validate');
        }
        
        // Fallback for unknown commands
        throw new Error(`Unsupported command: ${args[0]}`);
    }
    
    async pollTestStatus(testId) {
        if (!testId) return;
        
        try {
            const result = await this.callBridgeAPI(`/api/test/${testId}`);
            
            if (result.success && result.test_info) {
                const testInfo = result.test_info;
                
                // Update progress bar and details
                this.updateEnhancedProgress(testInfo);
                this.updateProgressDetails(`Phase: ${testInfo.current_phase || 'Running'} | ${testInfo.message || ''}`);
                
                // If test is still running, continue polling
                if (testInfo.status === 'running' || testInfo.status === 'starting') {
                    setTimeout(() => this.pollTestStatus(testId), 2000); // Poll every 2 seconds
                } else if (testInfo.status === 'completed') {
                    // Test completed, fetch final results
                    const finalResults = await this.callBridgeAPI(`/api/test/${testId}`);
                    if (finalResults.success && finalResults.test_info) {
                        this.testResults = finalResults.test_info; // Store final results
                        this.showResults(this.testResults);
                        this.updateProgress(100, 'Test completed!');
                        this.isTestRunning = false;
                        this.updateUI();
                    }
                } else if (
                    testInfo.status === 'failed' ||
                    testInfo.status === 'timeout' ||
                    testInfo.status === 'stopped' ||
                    testInfo.status === 'disconnected' ||
                    testInfo.status === 'unknown'
                ) {
                    // Test ended with an error, was stopped, or lost connection
                    this.handleTestStopped(`Test ended: ${testInfo.status}`);
                } else {
                    // Unknown status
                    this.handleTestStopped('Test ended (unknown status)');
                }
            } else {
                // Handle cases where test might have disappeared or API error
                console.error('Error fetching test status:', result.error);
                this.isTestRunning = false;
                this.currentTestId = null;
                this.updateProgress(0, 'Error fetching test status.');
                this.updateUI();
            }
        } catch (error) {
            console.error('Polling error:', error);
            // Assume test failed if polling errors out
            this.isTestRunning = false;
            this.currentTestId = null;
            this.updateProgress(0, 'Test polling failed.');
            this.updateUI();
        }
    }
    
    checkForActiveTest() {
        // Check if there's an active test when the app loads
        this.callBridgeAPI('/api/test/current')
            .then(result => {
                if (result.success && result.test_running) {
                    this.isTestRunning = true;
                    this.currentTestId = result.test_info.test_id;
                    this.currentTestDuration = result.test_info.estimated_duration || 0;

                    // Show background test notice
                    this.showBackgroundTestNotice(result.test_info);

                    // If test is disconnected/unknown, show cleanup UI and do not poll
                    if (
                        result.test_info.status === 'disconnected' ||
                        result.test_info.status === 'unknown'
                    ) {
                        this.showDisconnectedCleanupUI(result.test_info);
                        this.updateUI();
                        return;
                    }

                    // Update UI to reflect running state
                    this.updateUI();
                    // Start polling for status updates
                    this.pollTestStatus(this.currentTestId);
                } else {
                    // No test running, hide any notices
                    this.hideBackgroundTestNotice();
                }
            })
            .catch(error => {
                console.error('Error checking for active test:', error);
                this.hideBackgroundTestNotice();
            });
    }
    
    showBackgroundTestNotice(testInfo) {
        // Create or update background test notice
        let notice = document.getElementById('backgroundTestNotice');
        if (!notice) {
            notice = document.createElement('div');
            notice.id = 'backgroundTestNotice';
            notice.className = 'background-notice';
            document.body.appendChild(notice);
        }
        let extra = '';
        if (testInfo.status === 'disconnected' || testInfo.status === 'unknown') {
            extra = `<div style="margin-top:8px"><button id='cleanupDisconnectedTestBtn'>Clean up lost test</button></div>`;
        }
        
        notice.innerHTML = `
            <div class="notice-content">
                <div class="notice-header">
                    <i class="fas fa-spinner fa-spin"></i>
                    <strong>Test in Progress</strong>
                </div>
                <div class="notice-details">
                    <div class="test-info">
                        <span class="test-name">${this.getTestDisplayName(testType)}</span>
                        <span class="test-progress">${progress.toFixed(1)}% complete</span>
                    </div>
                    <div class="timing-info">
                        <span class="elapsed">Elapsed: ${this.formatDuration(elapsedTime)}</span>
                        <span class="remaining">Remaining: ${this.formatDuration(remainingTime)}</span>
                    </div>
                </div>
                <div class="notice-actions">
                    <button id="stopBackgroundTest" class="btn btn-danger btn-sm">
                        <i class="fas fa-stop"></i> Stop Test
                    </button>
                </div>
            </div>
        `;
        
        // Add event listener for stop button with proper context binding
        const stopButton = document.getElementById('stopBackgroundTest');
        if (stopButton) {
            // Remove any existing event listeners to prevent duplicates
            stopButton.replaceWith(stopButton.cloneNode(true));
            const newStopButton = document.getElementById('stopBackgroundTest');
            
            // Bind the context properly
            newStopButton.addEventListener('click', this.stopTest.bind(this));
        }
        
        notice.classList.remove('hidden');
    }
    
    hideBackgroundTestNotice() {
        const notice = document.getElementById('backgroundTestNotice');
        if (notice) {
            notice.classList.add('hidden');
        }
    }
    
    getTestDisplayName(testType) {
        const testNames = {
            'quick_max_speed': 'Quick Max Speed Test',
            'qlab_prores_422_show': 'ProRes 422 Show Simulation',
            'qlab_prores_hq_show': 'ProRes HQ Show Simulation',
            'max_sustained': 'Max Sustained Performance'
        };
        return testNames[testType] || testType;
    }
    
    exportResults() {
        if (!this.testResults) {
            alert('No test results to export.');
            return;
        }
        
        // Convert results to JSON string
        const jsonString = JSON.stringify(this.testResults, null, 2);
        
        // Create a Blob and trigger download
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `diskbench_results_${this.selectedDisk?.name || 'unknown'}_${this.selectedTestType}_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        
        // Clean up
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    
    switchTab(tabId) {
        // Hide all tab content sections
        document.querySelectorAll('.tab-content').forEach(section => {
            section.classList.add('hidden');
        });
        
        // Show the selected tab content
        document.getElementById(`${tabId}Section`).classList.remove('hidden');
        
        // Update active tab links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.getElementById(`${tabId}Tab`).classList.add('active');
        
        this.currentTab = tabId;
        
        // Special handling for setup tab
        if (tabId === 'setup') {
            this.updateSetupUI(); // Ensure setup UI is updated when tab is shown
        }
    }
}

// Initialize the application when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const app = new DiskBenchApp();
});
