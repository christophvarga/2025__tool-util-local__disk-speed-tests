/**
 * QLab Disk Performance Tester - Progress & Metrics Module
 * Progress bars, timing, real-time metrics updates.
 */

DiskBenchApp.prototype.updateProgress = function(percentage, message) {
    const validPercentage = Math.max(0, Math.min(100, percentage));
    document.getElementById('progressFill').style.width = `${validPercentage}%`;
    document.getElementById('progressText').textContent = message;
    this.lastValidProgress = validPercentage;
};

DiskBenchApp.prototype.updateProgressDetails = function(details) {
    document.getElementById('progressDetails').textContent = details;
};

DiskBenchApp.prototype.updateEnhancedProgress = function(testInfo) {
    if (!testInfo) return;

    const progress = testInfo.progress || 0;
    const elapsedTime = testInfo.elapsed_time || 0;
    const remainingTime = testInfo.remaining_time || 0;
    const estimatedDuration = testInfo.estimated_duration || this.currentTestDuration;

    if (testInfo.estimated_duration) this.currentTestDuration = testInfo.estimated_duration;

    const validElapsed = Math.max(0, elapsedTime);
    const validRemaining = Math.max(0, remainingTime);
    const validEstimated = Math.max(0, estimatedDuration);

    const validProgress = Math.max(0, Math.min(100, progress));
    if (Math.abs(validProgress - (this.lastValidProgress || 0)) > 0.5) {
        const phaseMessage = testInfo.test_phase_name || `Test running... ${validProgress.toFixed(1)}%`;
        this.updateProgress(validProgress, phaseMessage);
    }

    this.updateProgressTiming(validElapsed, validRemaining, validEstimated);

    if (testInfo.current_metrics) this.updateRealtimeMetrics(testInfo.current_metrics);
};

DiskBenchApp.prototype.updateProgressTiming = function(elapsed, remaining, total) {
    const elapsedEl = document.getElementById('elapsedTime');
    const remainingEl = document.getElementById('remainingTime');
    if (elapsedEl) elapsedEl.textContent = this.formatDuration(elapsed);
    if (remainingEl) remainingEl.textContent = this.formatDuration(remaining);

    const progressDetails = document.getElementById('progressDetails');
    if (progressDetails) {
        progressDetails.innerHTML = `
            <div class="timing-summary">
                Progress: ${this._escapeHTML(this.formatDuration(elapsed))} / ${this._escapeHTML(this.formatDuration(total))} (${this._escapeHTML(this.formatDuration(remaining))} remaining)
            </div>
        `;
    }
};

DiskBenchApp.prototype.updateRealtimeMetrics = function(metrics) {
    if (!metrics) return;

    const readEl = document.getElementById('currentReadSpeed');
    const writeEl = document.getElementById('currentWriteSpeed');
    const iopsEl = document.getElementById('currentIOPS');
    const latEl = document.getElementById('currentLatency');

    if (readEl) readEl.textContent = `${(metrics.read_mbps || 0).toFixed(1)} MB/s`;
    if (writeEl) writeEl.textContent = `${(metrics.write_mbps || 0).toFixed(1)} MB/s`;
    if (iopsEl) iopsEl.textContent = Math.round(metrics.iops || 0).toLocaleString();
    if (latEl) latEl.textContent = `${(metrics.latency_ms || 0).toFixed(2)} ms`;

    if (this.bandwidthChart) {
        const timestamp = new Date().toLocaleTimeString();
        this.bandwidthChart.data.labels.push(timestamp);
        this.bandwidthChart.data.datasets[0].data.push(metrics.read_mbps || 0);
        this.bandwidthChart.data.datasets[1].data.push(metrics.write_mbps || 0);

        if (this.bandwidthChart.data.labels.length > 60) {
            this.bandwidthChart.data.labels.shift();
            this.bandwidthChart.data.datasets.forEach(ds => ds.data.shift());
        }
        this.bandwidthChart.update('none');
    }
};
