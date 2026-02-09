/**
 * QLab Disk Performance Tester - Persistence & Export Module
 * LocalStorage, aliases, export, copy, download.
 */

DiskBenchApp.prototype.loadPersistedState = function() {
    try {
        const aliasRaw = localStorage.getItem('diskbench:aliases');
        this.diskAliases = aliasRaw ? JSON.parse(aliasRaw) : {};
    } catch (e) { this.diskAliases = {}; }
    try {
        const lastRaw = localStorage.getItem('diskbench:lastRun');
        this.lastRunParams = lastRaw ? JSON.parse(lastRaw) : null;
    } catch (e) { this.lastRunParams = null; }
};

DiskBenchApp.prototype.saveAliases = function() {
    try { localStorage.setItem('diskbench:aliases', JSON.stringify(this.diskAliases || {})); } catch (e) {}
};

DiskBenchApp.prototype.saveLastRun = function() {
    try { localStorage.setItem('diskbench:lastRun', JSON.stringify(this.lastRunParams || null)); } catch (e) {}
};

DiskBenchApp.prototype.getDiskAlias = function(devicePath) {
    if (!devicePath || !this.diskAliases) return '';
    return this.diskAliases[devicePath] || '';
};

DiskBenchApp.prototype.setDiskAlias = function(devicePath, alias) {
    if (!devicePath) return;
    if (!this.diskAliases) this.diskAliases = {};
    const trimmed = (alias || '').trim();
    if (trimmed) this.diskAliases[devicePath] = trimmed;
    else delete this.diskAliases[devicePath];
    this.saveAliases();
};

DiskBenchApp.prototype.exportResults = function() {
    if (!this.testResults) { alert('No test results to export.'); return; }
    const jsonString = JSON.stringify(this.testResults, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const diskLabel = this.getDiskAlias(this.selectedDisk?.device || '') || this.selectedDisk?.name || 'unknown';
    const safeDisk = this.sanitizeForFileName(diskLabel);
    const safeTest = this.sanitizeForFileName(this.selectedTestType || 'test');
    const date = new Date().toISOString().split('T')[0];
    a.download = `diskbench_results_${safeDisk}_${safeTest}_${date}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
};

DiskBenchApp.prototype.copyResults = function() {
    if (!this.testResults) { alert('No test results to copy.'); return; }
    const summaryText = this.buildResultsSummary(this.testResults);
    const fullText = `${summaryText}\n\nJSON:\n${JSON.stringify(this.testResults, null, 2)}`;

    const doCopiedUI = () => {
        const btn = document.getElementById('copyResults');
        if (!btn) return;
        const old = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
        btn.disabled = true;
        setTimeout(() => { btn.innerHTML = old; btn.disabled = false; }, 1500);
    };

    this._copyToClipboard(fullText, doCopiedUI);
};

DiskBenchApp.prototype.buildResultsSummary = function(results) {
    const testType = this.getTestDisplayName(this.selectedTestType || results.diskbench_test_type || results.test_type || 'unknown');
    const devicePath = this.selectedDisk?.device || results.params?.disk_path || results.disk_path || '';
    const alias = this.getDiskAlias(devicePath) || '';
    const diskName = alias || this.selectedDisk?.name || results.params?.disk_path || results.disk_path || 'Unknown';
    const diskDev = devicePath;
    const ts = results.end_time || results.test_time || new Date().toISOString();

    const s = (results?.fio_results?.summary) || (results?.result?.fio_results?.summary) ||
              (results?.result?.summary) || (results?.summary) || {};

    const readBW = ((s.total_read_bw || 0) / 1024);
    const writeBW = ((s.total_write_bw || 0) / 1024);
    const iops = (s.total_read_iops || s.iops || 0);
    const latency = (s.avg_read_latency || s.latency_avg || 0);

    return [
        'QLab Disk Performance Tester - Summary',
        `Test: ${testType}`,
        `Disk: ${diskName}${diskDev ? ` (${diskDev})` : ''}`,
        `Finished: ${new Date(ts).toLocaleString()}`,
        `Read: ${readBW.toFixed(0)} MB/s | Write: ${writeBW.toFixed(0)} MB/s | IOPS: ${iops.toFixed ? iops.toFixed(0) : iops} | Latency: ${latency.toFixed ? latency.toFixed(1) : latency} ms`
    ].join('\n');
};

DiskBenchApp.prototype.buildCliCommand = function(results) {
    const diskPath = this.selectedDisk?.device || results.params?.disk_path || results.disk_path || '/tmp';
    const selected = this.selectedTestType || results.diskbench_test_type || results.test_type || 'quick_max_speed';
    const map = {
        'quick_max_speed': 'quick_max_mix', 'qlab_prores_422_show': 'prores_422_real',
        'qlab_prores_hq_show': 'prores_422_hq_real', 'thermal_maximum_analyser': 'thermal_maximum'
    };
    const diskbenchTest = map[selected] || selected;
    const sizeGb = this.testSize || results.params?.size_gb || 10;
    const ts = new Date().toISOString().replace(/[:.]/g, '-');
    const outputFile = `/tmp/diskbench_${diskbenchTest}_${ts}.json`;
    return `python diskbench/main.py --test ${diskbenchTest} --disk '${diskPath}' --size ${sizeGb} --output '${outputFile}' --json --progress`;
};

DiskBenchApp.prototype.copyCli = function() {
    const results = this.testResults || {};
    const cli = this.buildCliCommand(results);
    const btn = document.getElementById('copyCli');
    const ok = () => {
        if (!btn) return;
        const old = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
        btn.disabled = true;
        setTimeout(() => { btn.innerHTML = old; btn.disabled = false; }, 1500);
    };
    this._copyToClipboard(cli, ok);
};

DiskBenchApp.prototype.downloadSummary = function() {
    if (!this.testResults) { alert('No test results to export.'); return; }
    const text = this.buildResultsSummary(this.testResults);
    const blob = new Blob([text + '\n'], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const diskLabel = this.getDiskAlias(this.selectedDisk?.device || '') || this.selectedDisk?.name || 'unknown';
    const safeDisk = this.sanitizeForFileName(diskLabel);
    const safeTest = this.sanitizeForFileName(this.selectedTestType || 'test');
    const date = new Date().toISOString().split('T')[0];
    a.download = `diskbench_summary_${safeDisk}_${safeTest}_${date}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
};

DiskBenchApp.prototype._copyToClipboard = function(text, onSuccess) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(onSuccess).catch(() => this._fallbackCopy(text, onSuccess));
    } else {
        this._fallbackCopy(text, onSuccess);
    }
};

DiskBenchApp.prototype._fallbackCopy = function(text, onSuccess) {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.cssText = 'position:fixed;left:-9999px';
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); } catch (e) {}
    document.body.removeChild(ta);
    if (onSuccess) onSuccess();
};
