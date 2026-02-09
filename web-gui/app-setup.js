/**
 * QLab Disk Performance Tester - Setup Wizard Module
 * System setup, FIO installation, validation.
 */

DiskBenchApp.prototype.checkSystemStatus = async function() {
    this.setupState.systemStatus = 'checking';
    this.updateSetupUI();

    try {
        const result = await this.callBridgeAPI('/api/status');
        if (result.success) {
            this.setupState.fioAvailable = result.fio_available || false;
            this.setupState.fioWorking = result.fio_working || false;
            this.setupState.diskAccess = result.disk_access || false;
            this.setupState.systemStatus = 'checked';
            this.setupState.setupStep = this.setupState.fioWorking ? 3 : 2;
        } else {
            throw new Error(result.error || 'Failed to get system status');
        }
    } catch (error) {
        console.error('Error checking system status:', error);
        this.setupState.systemStatus = 'error';
        this.setupState.setupStep = 1;
    } finally {
        this.updateSetupUI();
    }
};

DiskBenchApp.prototype.startInstallation = async function() {
    this.setupState.installationInProgress = true;
    this.setupState.setupStep = 2;
    this.updateSetupUI();

    try {
        const result = await this.callBridgeAPI('/api/setup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'install_fio' })
        });
        if (result.success) {
            await this.checkSystemStatus();
            this.setupState.setupStep = 3;
        } else {
            throw new Error(result.error || 'Installation failed');
        }
    } catch (error) {
        console.error('Installation error:', error);
        this.setupState.setupStep = 2;
        this.showSetupError(`Installation failed: ${error.message}`);
    } finally {
        this.setupState.installationInProgress = false;
        this.updateSetupUI();
    }
};

DiskBenchApp.prototype.runValidation = async function() {
    this.setupState.setupStep = 3;
    this.updateSetupUI();

    try {
        const result = await this.callBridgeAPI('/api/validate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'run_all_tests' })
        });
        if (result.success && result.overall_status === 'passed') {
            this.setupState.setupStep = 4;
        } else if (result.success && result.overall_status === 'failed') {
            this.setupState.setupStep = 3;
            this.showSetupError(`Validation failed: ${result.tests.filter(t => !t.passed).map(t => t.name).join(', ')}`);
        } else {
            throw new Error(result.error || 'Validation process failed');
        }
    } catch (error) {
        console.error('Validation error:', error);
        this.setupState.setupStep = 3;
        this.showSetupError(`Validation error: ${error.message}`);
    } finally {
        this.updateSetupUI();
    }
};

DiskBenchApp.prototype.closeSetup = function() {
    document.getElementById('setupWizard').classList.add('hidden');
    document.getElementById('testingSection').classList.remove('hidden');
    this.currentTab = 'testing';
};

DiskBenchApp.prototype.skipSetup = function() {
    this.setupState.setupStep = 4;
    this.updateSetupUI();
    this.closeSetup();
};

DiskBenchApp.prototype.retrySetup = function() {
    this.setupState = {
        systemStatus: 'checking', fioAvailable: false, fioWorking: false,
        diskAccess: false, setupStep: 1, installationInProgress: false
    };
    this.checkSystemStatus();
    this.updateSetupUI();
};

DiskBenchApp.prototype.updateSetupUI = function() {
    const setupWizard = document.getElementById('setupWizard');
    const testingSection = document.getElementById('testingSection');

    if (this.currentTab === 'setup') {
        setupWizard.classList.remove('hidden');
        testingSection.classList.add('hidden');
    } else {
        setupWizard.classList.add('hidden');
        testingSection.classList.remove('hidden');
    }

    ['step1Indicator', 'step2Indicator', 'step3Indicator', 'step4Indicator'].forEach((id, i) => {
        document.getElementById(id).classList.toggle('active', this.setupState.setupStep >= i + 1);
    });

    document.getElementById('statusMessage').textContent = this.getSetupStatusMessage();
    document.getElementById('fioStatus').textContent = this.getFIOStatus();
    document.getElementById('diskStatus').textContent = this.getDiskAccessStatus();

    document.getElementById('startInstallation').disabled = this.setupState.installationInProgress || this.setupState.setupStep >= 2;
    document.getElementById('runValidation').disabled = this.setupState.installationInProgress || this.setupState.setupStep < 3 || this.setupState.setupStep >= 4;
    document.getElementById('closeSetup').disabled = this.setupState.setupStep < 4;
    document.getElementById('skipSetup').disabled = this.setupState.setupStep >= 4;
    document.getElementById('retrySetup').disabled = this.setupState.installationInProgress;

    document.getElementById('installationProgress').classList.toggle('hidden', !this.setupState.installationInProgress);
    document.getElementById('setupCompleteMessage').classList.toggle('hidden', this.setupState.setupStep < 4);
};

DiskBenchApp.prototype.getSetupStatusMessage = function() {
    if (this.setupState.systemStatus === 'checking') return 'Checking system status...';
    if (this.setupState.systemStatus === 'error') return 'Error checking system status.';
    if (this.setupState.setupStep === 4) return 'System setup complete!';
    return 'System status checked.';
};

DiskBenchApp.prototype.getFIOStatus = function() {
    if (this.setupState.fioAvailable) {
        return this.setupState.fioWorking ? '✅ FIO is installed and working correctly.' : '⚠️ FIO is installed but has issues (shared memory).';
    }
    return '❌ FIO is not installed or not found.';
};

DiskBenchApp.prototype.getDiskAccessStatus = function() {
    return this.setupState.diskAccess ? '✅ Disk access is permitted.' : '❌ Disk access denied or unavailable.';
};

DiskBenchApp.prototype.showSetupError = function(message) {
    const errorElement = document.getElementById('setupErrorMessage');
    errorElement.textContent = message;
    errorElement.classList.remove('hidden');
};

DiskBenchApp.prototype.showDisconnectedCleanupUI = function(testInfo) {
    console.warn('Disconnected test detected:', testInfo);
    this.updateProgress(0, `Test ${testInfo.test_id || 'unknown'} was disconnected. Clean up to start a new test.`);
    document.getElementById('progressSection').classList.remove('hidden');
    document.getElementById('stopTest').classList.remove('hidden');
};
