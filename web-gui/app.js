/**
 * QLab Disk Performance Tester - Entry Point
 *
 * Module loading order (all via <script> in index.html):
 *   1. app-core.js       - Class definition, constructor, init, utilities
 *   2. app-api.js         - Bridge API, polling, circuit breaker
 *   3. app-disks.js       - Disk/test management, test control
 *   4. app-progress.js    - Progress bars, timing, real-time metrics
 *   5. app-results.js     - Result rendering, analysis views
 *   6. app-setup.js       - Setup wizard, FIO installation
 *   7. app-persistence.js - LocalStorage, export, clipboard
 *   8. app.js (this file) - Bootstrap + global helpers
 */

// Initialize the application when DOM is ready
document.addEventListener('DOMContentLoaded', function () {
    const app = new DiskBenchApp();
    window.app = app;
});

// Global functions for pattern info modal
function showPatternInfo(testType) {
    const modal = document.getElementById('patternInfoModal');
    const title = document.getElementById('modalTitle');
    const body = document.getElementById('modalBody');

    let content = '';

    const _e = (s) => {
        if (window.app && window.app._escapeHTML) return window.app._escapeHTML(s);
        const div = document.createElement('div');
        div.textContent = String(s ?? '');
        return div.innerHTML;
    };

    const catalog = window.app && window.app.testsCatalog;
    if (catalog && catalog.tests && catalog.tests[testType]) {
        const t = catalog.tests[testType];
        title.textContent = t.name || testType;
        const minutes = t.duration ? Math.round(t.duration / 60) : null;
        const durationText = minutes ? `${minutes} Minuten` : 'Unbekannt';
        content = `
            <div class="pattern-overview">
                <h4>${t.display_label ? `${_e(t.display_label)}: ` : ''}${_e(t.name || testType)}</h4>
                <p>${_e(t.description || '')}</p>
            </div>
            <div class="technical-specs">
                <strong>Dauer:</strong> ${_e(durationText)}
            </div>
        `;
    } else {
        switch (testType) {
            case 'quick_max_speed':
                title.textContent = 'Quick Max Speed Test';
                content = `
                    <h4>Quick Max Speed Test</h4>
                    <p><strong>Duration:</strong> 1 minute</p>
                    <p><strong>Purpose:</strong> Basic disk performance check and system validation</p>
                    <p><strong>Note:</strong> This is NOT a QLab-specific test</p>
                `;
                break;
            default:
                title.textContent = 'Test Information';
                content = '<p>Information not available for this test type.</p>';
        }
    }

    body.innerHTML = content;
    modal.classList.remove('hidden');
}

function closePatternInfo() {
    const modal = document.getElementById('patternInfoModal');
    modal.classList.add('hidden');
}
