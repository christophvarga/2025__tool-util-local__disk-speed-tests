/**
 * QLab Disk Performance Tester - Results Module
 * Result rendering, analysis views, recommendations.
 */

DiskBenchApp.prototype.showResults = function(results) {
    document.getElementById('resultsSection').classList.remove('hidden');
    document.getElementById('exportResults').classList.remove('hidden');
    ['copyResults', 'copyCli', 'downloadSummary'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.remove('hidden');
    });

    const testType = this.selectedTestType;
    const renderers = {
        'quick_max_speed': 'renderTest1Analysis',
        'qlab_prores_422_show': 'renderTest2Analysis',
        'qlab_prores_hq_show': 'renderTest3Analysis',
        'thermal_maximum_analyser': 'renderThermalMaximumAnalysis'
    };
    const renderer = renderers[testType] || 'renderGenericAnalysis';
    this[renderer](results);
    this.renderImplementationDetails(results);
};

DiskBenchApp.prototype.renderQLabAnalysis = function(analysis) {
    const container = document.getElementById('qlabAnalysis');
    if (!analysis) { container.innerHTML = '<p>No analysis data available.</p>'; return; }

    const overallClass = this.getPerformanceClass(analysis.overall_performance || analysis.performance_class);
    container.className = `qlab-analysis ${overallClass}`;
    container.innerHTML = `
        <div class="analysis-header">
            <h3 class="analysis-title">QLab Performance Analysis</h3>
            <div class="analysis-badge ${this._escapeHTML(overallClass)}">
                ${this._escapeHTML(this.getPerformanceMessage(analysis.overall_performance || analysis.performance_class))}
            </div>
        </div>
        <div class="analysis-grid">
            <div class="analysis-section"><h4>Performance Indicators</h4><ul>${this.renderAnalysisDetails(analysis)}</ul></div>
            <div class="analysis-section"><h4>Recommendations</h4><ul>${this.renderRecommendations(analysis)}</ul></div>
        </div>
    `;
};

DiskBenchApp.prototype.renderAnalysisDetails = function(analysis) {
    const details = [];
    if (analysis.read_performance) details.push(`${this.getPerformanceIcon(analysis.read_performance)} Read Performance: ${this._escapeHTML(analysis.read_performance)}`);
    if (analysis.write_performance) details.push(`${this.getPerformanceIcon(analysis.write_performance)} Write Performance: ${this._escapeHTML(analysis.write_performance)}`);
    if (analysis.latency_performance) details.push(`${this.getPerformanceIcon(analysis.latency_performance)} Latency Performance: ${this._escapeHTML(analysis.latency_performance)}`);
    return details.map(d => `<li>${d}</li>`).join('');
};

DiskBenchApp.prototype.renderRecommendations = function() {
    return ['✅ Good performance for most QLab applications', '✅ Suitable for standard video playback', '💡 Consider SSD upgrade for demanding applications'].map(r => `<li>${r}</li>`).join('');
};

DiskBenchApp.prototype.renderDetailedMetrics = function(fioResults) {
    const container = document.getElementById('detailedMetrics');
    if (!fioResults || !fioResults.summary) { container.innerHTML = '<p>No detailed metrics available.</p>'; return; }
    const s = fioResults.summary;
    const metrics = [
        { title: 'Sequential Read', value: this.formatNumber(s.total_read_bw || 0), unit: 'MB/s', details: `${this.formatNumber(s.total_read_iops || 0)} IOPS` },
        { title: 'Sequential Write', value: this.formatNumber(s.total_write_bw || 0), unit: 'MB/s', details: `${this.formatNumber(s.total_write_iops || 0)} IOPS` },
        { title: 'Read Latency', value: this.formatNumber(s.avg_read_latency || 0), unit: 'ms', details: 'Average latency' },
        { title: 'Write Latency', value: this.formatNumber(s.avg_write_latency || 0), unit: 'ms', details: 'Average latency' }
    ];
    container.innerHTML = metrics.map(m => `<div class="metric-card"><h4>${this._escapeHTML(m.title)}</h4><div class="metric-value">${this._escapeHTML(m.value)}</div><div class="metric-unit">${this._escapeHTML(m.unit)}</div><div class="metric-details">${this._escapeHTML(m.details)}</div></div>`).join('');
};

DiskBenchApp.prototype.renderImplementationDetails = function(results) {
    const container = document.getElementById('implementationInfo');
    const testInfo = results.test_info || {};
    const alias = this.getDiskAlias(testInfo.disk_path || this.selectedDisk?.device || '') || '';
    const aliasLine = alias ? `<p><strong>Disk label:</strong> ${this._escapeHTML(alias)}</p>` : '';
    container.innerHTML = `
        <p><strong>Test executed:</strong> ${this._escapeHTML(testInfo.test_name || 'Unknown')} on ${this._escapeHTML(testInfo.disk_path || 'Unknown')}</p>
        ${aliasLine}
        <p><strong>Timestamp:</strong> ${this._escapeHTML(testInfo.timestamp ? new Date(testInfo.timestamp).toLocaleString() : 'Unknown')}</p>
        <p><strong>CLI Command:</strong> <code>diskbench --test ${this._escapeHTML(this.selectedTestType)} --disk ${this._escapeHTML(this.selectedDisk?.device)} --output result.json</code></p>
        <p><strong>Architecture:</strong> Web GUI → Helper Binary → FIO Engine → JSON Results</p>
    `;
};

DiskBenchApp.prototype.renderTest1Analysis = function(results) {
    const container = document.getElementById('qlabAnalysis');
    const summary = results.fio_results?.summary || {};
    document.getElementById('detailedMetrics').innerHTML = '';

    const readBW = (summary.total_read_bw || 0) / 1024;
    const writeBW = (summary.total_write_bw || 0) / 1024;
    const readIOPS = summary.total_read_iops || 0;
    const avgLatency = summary.avg_read_latency || 0;

    let performanceClass, classColor, description;
    if (readBW > 2000) { performanceClass = 'HIGH-END SSD'; classColor = 'excellent'; description = 'Excellent disk performance detected'; }
    else if (readBW > 1000) { performanceClass = 'GOOD SSD'; classColor = 'good'; description = 'Good disk performance detected'; }
    else if (readBW > 500) { performanceClass = 'STANDARD SSD'; classColor = 'warning'; description = 'Standard disk performance detected'; }
    else if (readBW > 100) { performanceClass = 'BASIC DISK'; classColor = 'warning'; description = 'Basic disk performance detected'; }
    else { performanceClass = 'SLOW DISK'; classColor = 'danger'; description = 'Limited disk performance detected'; }

    const _e = (s) => this._escapeHTML(s);
    container.innerHTML = `
        <div class="test-analysis-header"><h3>📊 Test 1: Quick Setup & Performance Check</h3>
            <div class="test-load-info"><strong>Test Duration:</strong> 1 minute quick assessment<br><strong>Purpose:</strong> Basic disk performance check and system validation<br><strong>Note:</strong> This is NOT a QLab-specific test</div>
            <div class="tier-badge ${_e(classColor)}">⚡ ${_e(performanceClass)}</div>
        </div>
        <div class="basic-metrics"><h4>📈 Basic Performance Metrics</h4><div class="metrics-grid">
            <div class="metric-item"><div class="metric-label">Sequential Read</div><div class="metric-value-with-bar"><div class="metric-value-large">${_e(readBW.toFixed(0))}</div><div class="metric-unit-inline">MB/s</div></div><div class="performance-bar-container"><div class="performance-bar ${_e(classColor)}" style="width: ${Math.min(100, (readBW / 3000) * 100)}%"></div></div><div class="metric-benchmark">Max theoretical: ~3000 MB/s</div></div>
            <div class="metric-item"><div class="metric-label">Sequential Write</div><div class="metric-value-with-bar"><div class="metric-value-large">${_e(writeBW.toFixed(0))}</div><div class="metric-unit-inline">MB/s</div></div><div class="performance-bar-container"><div class="performance-bar ${_e(classColor)}" style="width: ${Math.min(100, (writeBW / 3000) * 100)}%"></div></div><div class="metric-benchmark">Max theoretical: ~3000 MB/s</div></div>
            <div class="metric-item"><div class="metric-label">Random Access</div><div class="metric-value-with-bar"><div class="metric-value-large">${_e(this.formatNumber(readIOPS))}</div><div class="metric-unit-inline">IOPS</div></div><div class="performance-bar-container"><div class="performance-bar ${_e(classColor)}" style="width: ${Math.min(100, (readIOPS / 100000) * 100)}%"></div></div><div class="metric-benchmark">Max theoretical: ~100k IOPS</div></div>
            <div class="metric-item"><div class="metric-label">Response Time</div><div class="metric-value-with-bar"><div class="metric-value-large">${_e(avgLatency.toFixed(1))}</div><div class="metric-unit-inline">ms</div></div><div class="performance-bar-container"><div class="performance-bar ${_e(this.getLatencyClass(avgLatency))}" style="width: ${100 - Math.min(100, (avgLatency / 20) * 100)}%"></div></div><div class="metric-benchmark">Lower is better (target: &lt;5ms)</div></div>
        </div></div>
        <div class="system-assessment"><h4>🔧 System Assessment</h4><div class="assessment-summary ${_e(classColor)}"><div class="assessment-result">${_e(description)}</div><div class="assessment-note">This quick test provides a basic performance overview. For QLab-specific analysis, run Test 2 or Test 3.</div></div></div>
        <div class="next-steps"><h4>➡️ Next Steps</h4><div class="recommendation-list">
            <div class="recommendation-item">📋 <strong>System Check Complete:</strong> Basic disk performance measured</div>
            <div class="recommendation-item">🎬 <strong>For QLab Analysis:</strong> Run Test 2 (ProRes 422) or Test 3 (ProRes HQ)</div>
            <div class="recommendation-item">⚡ <strong>For Sustained Performance:</strong> Run Test 4 (Max Sustained)</div>
            <div class="recommendation-item">💡 <strong>Performance Class:</strong> ${_e(performanceClass)} - ${_e(description.toLowerCase())}</div>
        </div></div>
    `;
};

DiskBenchApp.prototype._renderQLabTestAnalysis = function(results, title, requiredBW) {
    const container = document.getElementById('qlabAnalysis');
    const summary = results.fio_results?.summary || {};
    document.getElementById('detailedMetrics').innerHTML = '';

    const readBW = (summary.total_read_bw || 0) / 1024;
    const minBW = (summary.min_read_bw || readBW) / 1024;
    const maxBW = (summary.max_read_bw || readBW) / 1024;
    const avgLatency = summary.avg_read_latency || 0;
    const performanceTier = this.getQLabPerformanceTier(readBW, requiredBW);

    const _e = (s) => this._escapeHTML(s);
    container.innerHTML = `
        <div class="test-analysis-header"><h3>${_e(title)}</h3>
            <div class="tier-badge ${_e(performanceTier.class)}">${_e(performanceTier.message)}</div>
        </div>
        <div class="qlab-metrics"><h4>📊 QLab Performance Metrics</h4><div class="metrics-grid">
            <div class="metric-item"><div class="metric-label">Average Read Speed</div><div class="metric-value">${_e(readBW.toFixed(0))} MB/s</div><div class="metric-status">Overall average</div></div>
            <div class="metric-item"><div class="metric-label">Min Read Speed</div><div class="metric-value">${_e(minBW.toFixed(0))} MB/s</div><div class="metric-status">Lowest sustained speed</div></div>
            <div class="metric-item"><div class="metric-label">Max Read Speed</div><div class="metric-value">${_e(maxBW.toFixed(0))} MB/s</div><div class="metric-status">Peak speed during test</div></div>
            <div class="metric-item"><div class="metric-label">Average Latency</div><div class="metric-value">${_e(avgLatency.toFixed(1))} ms</div><div class="metric-status">Cue response time</div></div>
        </div></div>
        <div class="qlab-analysis"><h4>💡 QLab Performance Analysis</h4><div class="analysis-grid">
            <div class="analysis-section"><h5>Performance Tier</h5><ul><li>${_e(performanceTier.message)}</li></ul></div>
            <div class="analysis-section"><h5>Recommendations</h5><ul>${this.generateQLabRecommendations(readBW, avgLatency, performanceTier.tier)}</ul></div>
        </div></div>
    `;
};

DiskBenchApp.prototype.renderTest2Analysis = function(results) {
    this._renderQLabTestAnalysis(results, '🎬 Test 2: ProRes 422 Show Simulation', 220);
};

DiskBenchApp.prototype.renderTest3Analysis = function(results) {
    this._renderQLabTestAnalysis(results, '🎬 Test 3: ProRes HQ Show Simulation', 440);
};

DiskBenchApp.prototype.renderThermalMaximumAnalysis = function(results) {
    this._renderQLabTestAnalysis(results, '🔥 Thermal Maximum Analyser', 300);
};

DiskBenchApp.prototype.renderGenericAnalysis = function(results) {
    const container = document.getElementById('qlabAnalysis');
    const summary = results.fio_results?.summary || {};
    document.getElementById('detailedMetrics').innerHTML = '';

    const readBW = (summary.total_read_bw || 0) / 1024;
    const avgLatency = summary.avg_read_latency || 0;
    const _e = (s) => this._escapeHTML(s);
    container.innerHTML = `
        <div class="test-analysis-header"><h3>❓ Unknown Test Type Analysis</h3>
            <div class="test-load-info"><strong>Test Type:</strong> ${_e(this.selectedTestType)}<br><strong>Purpose:</strong> Generic performance assessment</div>
        </div>
        <div class="basic-metrics"><h4>📈 Basic Performance Metrics</h4><div class="metrics-grid">
            <div class="metric-item"><div class="metric-label">Sequential Read</div><div class="metric-value">${_e(readBW.toFixed(0))} MB/s</div><div class="metric-status">Overall average</div></div>
            <div class="metric-item"><div class="metric-label">Average Latency</div><div class="metric-value">${_e(avgLatency.toFixed(1))} ms</div><div class="metric-status">Average latency</div></div>
        </div></div>
        <div class="next-steps"><h4>➡️ Next Steps</h4><div class="recommendation-list"><div class="recommendation-item">❓ Unknown test type. Please select a known test.</div></div></div>
    `;
};

DiskBenchApp.prototype.generateTest1Recommendations = function(readBW, latency, tier) {
    const recs = [];
    if (tier === 'FLAGSHIP') { recs.push('🏆 Excellent for any QLab production'); recs.push('🎯 Run Test 2 & 3 to confirm sustained performance'); }
    else if (tier === 'PROFESSIONAL') { recs.push('🥇 Great for ProRes 422 production workflows'); recs.push('🎯 Test ProRes HQ scenarios with Test 3'); }
    else if (tier === 'STANDARD') { recs.push('🥈 Suitable for HD and conservative 4K workflows'); recs.push('⚠️ Avoid complex crossfades'); }
    else if (tier === 'BASIC') { recs.push('🥉 Limited to HD production only'); recs.push('💡 Consider SSD upgrade'); }
    else { recs.push('❌ Not suitable for professional QLab production'); recs.push('🔧 Storage upgrade required'); }
    if (latency > 10) recs.push('⚠️ High latency may affect cue triggering');
    recs.push('📈 Next: Run Test 2 (ProRes 422 Show) for realistic show simulation');
    return recs.map(r => `<div class="recommendation-item">${r}</div>`).join('');
};

DiskBenchApp.prototype.generateQLabRecommendations = function(readBW, avgLatency, tier) {
    const recs = [];
    if (tier === 'FLAGSHIP') { recs.push('<li>🏆 Excellent for complex QLab productions</li>', '<li>✅ Suitable for demanding crossfades</li>', '<li>🎯 Perfect for professional productions</li>'); }
    else if (tier === 'PROFESSIONAL') { recs.push('<li>🥇 Great for standard QLab productions</li>', '<li>✅ Handles most ProRes workflows</li>', '<li>⚠️ Test complex scenarios before critical shows</li>'); }
    else if (tier === 'STANDARD') { recs.push('<li>🥈 Suitable for basic QLab workflows</li>', '<li>⚠️ Avoid complex crossfades</li>', '<li>💡 Consider limiting to HD content</li>'); }
    else { recs.push('<li>❌ Not recommended for professional QLab use</li>', '<li>🔧 Storage upgrade strongly recommended</li>', '<li>⚠️ May experience dropouts</li>'); }
    if (avgLatency > 10) recs.push('<li>⚠️ High latency may affect cue triggering</li>');
    if (readBW < 100) recs.push('<li>🚨 Very low bandwidth - unsuitable for video playback</li>');
    return recs.join('');
};
