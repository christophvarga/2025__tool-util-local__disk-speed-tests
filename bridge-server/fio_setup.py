"""Mixin: FIO SHM detection, compilation, installation, auto-fix."""
import os, subprocess
from datetime import datetime


def _mklog(logs, logger):
    """Return a log_cb helper that appends to *logs* and logs to *logger*."""
    def log_cb(level, msg):
        logs.append({'timestamp': datetime.now().strftime('%H:%M:%S'),
                     'level': level, 'message': msg})
        logger.info(f"[{level.upper()}] {msg}")
    return log_cb


class FioSetupMixin:
    """Detect, compile, and install a no-SHM FIO binary."""

    def detect_fio_shm_support(self):
        """Detect if standard FIO has shared memory issues on macOS."""
        logs = []
        log_cb = _mklog(logs, self.logger)

        try:
            log_cb('info', 'Testing FIO shared memory support')
            fio_path = None
            for p in ['/opt/homebrew/bin/fio', '/usr/local/bin/fio']:
                if os.path.exists(p) and os.access(p, os.X_OK):
                    fio_path = p
                    break
            if not fio_path:
                import shutil
                fio_path = shutil.which('fio')
            if not fio_path:
                log_cb('warning', 'No standard FIO found')
                return {
                    'success': True, 'has_shm_issues': True,
                    'reason': 'no_fio_found', 'needs_compilation': True, 'logs': logs,
                }

            log_cb('info', f'Testing FIO at: {fio_path}')
            test_file = '/tmp/fio_shm_test'
            with open(test_file, 'wb') as f:
                f.write(b'0' * (1024 * 1024))
            try:
                fio_cmd = [
                    fio_path, '--name=shm_test', f'--filename={test_file}',
                    '--size=1M', '--bs=4k', '--rw=read', '--runtime=1',
                    '--time_based=1', '--ioengine=libaio', '--direct=1',
                    '--numjobs=2', '--group_reporting=1', '--output-format=json',
                ]
                env = os.environ.copy()
                env['TMPDIR'] = '/tmp'
                result = subprocess.run(
                    fio_cmd, capture_output=True, text=True, timeout=10, env=env,
                )
                log_cb('info', f'SHM test rc: {result.returncode}')
                if result.stderr:
                    log_cb('info', f'FIO STDERR: {result.stderr}')

                shm_patterns = [
                    'failed to setup shm segment', 'shm_open',
                    'shared memory', 'Cannot allocate memory',
                ]
                has_shm = any(p in result.stderr for p in shm_patterns)

                if result.returncode != 0 and has_shm:
                    log_cb('warning', 'Standard FIO has shared memory issues')
                    return {
                        'success': True, 'has_shm_issues': True,
                        'reason': 'shm_error_detected',
                        'error_details': result.stderr,
                        'needs_compilation': True,
                        'fio_path': fio_path, 'logs': logs,
                    }
                elif result.returncode == 0:
                    log_cb('info', 'Standard FIO works fine')
                    return {
                        'success': True, 'has_shm_issues': False,
                        'reason': 'fio_works_fine', 'needs_compilation': False,
                        'fio_path': fio_path, 'logs': logs,
                    }
                else:
                    log_cb('warning', f'FIO failed rc {result.returncode}')
                    return {
                        'success': True, 'has_shm_issues': True,
                        'reason': 'fio_failed_unknown',
                        'error_details': result.stderr,
                        'needs_compilation': True,
                        'fio_path': fio_path, 'logs': logs,
                    }
            finally:
                if os.path.exists(test_file):
                    os.remove(test_file)
        except Exception as e:
            log_cb('error', f'SHM detection failed: {e}')
            return {'success': False, 'error': str(e), 'logs': logs}

    def install_build_dependencies(self):
        """Install dependencies needed for FIO compilation."""
        logs = []
        log_cb = _mklog(logs, self.logger)

        try:
            log_cb('info', 'Installing build dependencies')
            import shutil
            brew_path = shutil.which('brew')
            if not brew_path:
                log_cb('error', 'Homebrew not found')
                return {'success': False, 'error': 'Homebrew not found', 'logs': logs}

            for pkg in ['automake', 'libtool', 'pkg-config']:
                log_cb('info', f'Installing {pkg}...')
                r = subprocess.run(
                    [brew_path, 'install', pkg],
                    capture_output=True, text=True, timeout=300,
                )
                if r.returncode == 0:
                    log_cb('info', f'{pkg} installed successfully')
                elif 'already installed' in r.stderr or 'already installed' in r.stdout:
                    log_cb('info', f'{pkg} already installed')
                else:
                    log_cb('warning', f'{pkg} installation had issues: {r.stderr}')

            r = subprocess.run(
                ['xcode-select', '--version'],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode == 0:
                log_cb('info', 'Xcode Command Line Tools available')
            else:
                log_cb('warning', 'Xcode CLT not found')
                return {
                    'success': False,
                    'error': 'Xcode Command Line Tools required', 'logs': logs,
                }
            return {'success': True, 'message': 'Build dependencies installed', 'logs': logs}
        except subprocess.TimeoutExpired:
            log_cb('error', 'Dependency installation timed out')
            return {'success': False, 'error': 'Installation timed out', 'logs': logs}
        except Exception as e:
            log_cb('error', f'Dependency installation failed: {e}')
            return {'success': False, 'error': str(e), 'logs': logs}

    def compile_fio_no_shm(self):
        """Download and compile FIO without shared memory support."""
        logs = []
        log_cb = _mklog(logs, self.logger)

        try:
            log_cb('info', 'Starting FIO compilation without shared memory')
            import tempfile, shutil
            build_dir = tempfile.mkdtemp(prefix='fio_build_')
            log_cb('info', f'Build directory: {build_dir}')
            try:
                log_cb('info', 'Downloading FIO source code...')
                r = subprocess.run(
                    ['git', 'clone', '--depth', '1',
                     'https://github.com/axboe/fio.git',
                     os.path.join(build_dir, 'fio')],
                    capture_output=True, text=True, timeout=300,
                )
                if r.returncode != 0:
                    log_cb('error', f'Git clone failed: {r.stderr}')
                    return {'success': False, 'error': f'Clone failed: {r.stderr}', 'logs': logs}

                fio_src = os.path.join(build_dir, 'fio')
                log_cb('info', 'Configuring FIO without shared memory...')
                r = subprocess.run(
                    ['./configure', '--disable-shm'],
                    cwd=fio_src, capture_output=True, text=True, timeout=120,
                )
                if r.returncode != 0:
                    return {'success': False, 'error': f'Configure failed: {r.stderr}', 'logs': logs}

                log_cb('info', 'Compiling FIO...')
                r = subprocess.run(
                    ['make', '-j4'], cwd=fio_src,
                    capture_output=True, text=True, timeout=600,
                )
                if r.returncode != 0:
                    return {'success': False, 'error': f'Make failed: {r.stderr}', 'logs': logs}

                fio_bin = os.path.join(fio_src, 'fio')
                if not os.path.exists(fio_bin):
                    return {'success': False, 'error': 'FIO binary not created', 'logs': logs}

                r = subprocess.run(
                    [fio_bin, '--version'],
                    capture_output=True, text=True, timeout=10,
                )
                if r.returncode != 0:
                    return {'success': False, 'error': 'Compiled FIO not functional', 'logs': logs}
                version_info = r.stdout.strip()
                log_cb('info', f'Compiled FIO version: {version_info}')

                target_path = '/usr/local/bin/fio-nosmh'
                try:
                    shutil.copy2(fio_bin, target_path)
                except PermissionError:
                    ir = subprocess.run(
                        ['sudo', 'cp', fio_bin, target_path],
                        capture_output=True, text=True, timeout=30,
                    )
                    if ir.returncode != 0:
                        return {'success': False, 'error': f'Install failed: {ir.stderr}', 'logs': logs}

                subprocess.run(['chmod', '+x', target_path],
                    capture_output=True, text=True, timeout=10)

                ft = subprocess.run(
                    [target_path, '--version'],
                    capture_output=True, text=True, timeout=10,
                )
                if ft.returncode == 0:
                    log_cb('info', 'FIO installation successful!')
                    return {
                        'success': True,
                        'message': 'FIO compiled and installed without shared memory',
                        'fio_path': target_path, 'version': ft.stdout.strip(),
                        'build_dir': build_dir, 'logs': logs,
                    }
                return {'success': False, 'error': 'Installed FIO not functional', 'logs': logs}
            finally:
                try:
                    shutil.rmtree(build_dir)
                    log_cb('info', 'Build directory cleaned up')
                except Exception as e:
                    log_cb('warning', f'Failed to cleanup build dir: {e}')
        except subprocess.TimeoutExpired:
            log_cb('error', 'FIO compilation timed out')
            return {'success': False, 'error': 'Compilation timed out', 'logs': logs}
        except Exception as e:
            log_cb('error', f'FIO compilation failed: {e}')
            return {'success': False, 'error': str(e), 'logs': logs}

    def auto_fix_fio_shm(self):
        """Automatically detect and fix FIO shared memory issues."""
        logs = []
        log_cb = _mklog(logs, self.logger)

        try:
            log_cb('info', 'Starting automatic FIO shared memory fix')
            nosmh = '/usr/local/bin/fio-nosmh'
            if os.path.exists(nosmh) and os.access(nosmh, os.X_OK):
                log_cb('info', 'FIO no-shm version already installed')
                return {
                    'success': True,
                    'message': 'FIO no-shm version already available',
                    'fio_path': nosmh, 'action': 'already_installed', 'logs': logs,
                }

            log_cb('info', 'Step 1: Detecting FIO shared memory support...')
            shm = self.detect_fio_shm_support()
            if not shm.get('success'):
                return {
                    'success': False,
                    'error': shm.get('error', 'SHM detection failed'),
                    'logs': logs + shm.get('logs', []),
                }
            if not shm.get('needs_compilation'):
                log_cb('info', 'Standard FIO works fine - no fix needed')
                return {
                    'success': True,
                    'message': 'Standard FIO works without issues',
                    'fio_path': shm.get('fio_path'),
                    'action': 'no_fix_needed',
                    'logs': logs + shm.get('logs', []),
                }

            log_cb('info', 'Step 2: Installing build dependencies...')
            deps = self.install_build_dependencies()
            if not deps.get('success'):
                return {
                    'success': False,
                    'error': f"Failed to install deps: {deps.get('error')}",
                    'logs': logs + deps.get('logs', []),
                }

            log_cb('info', 'Step 3: Compiling FIO without shared memory...')
            comp = self.compile_fio_no_shm()
            if not comp.get('success'):
                return {
                    'success': False,
                    'error': f"Compilation failed: {comp.get('error')}",
                    'logs': logs + comp.get('logs', []),
                }

            log_cb('info', 'FIO compilation and installation completed!')
            return {
                'success': True,
                'message': 'FIO compiled and installed without shared memory',
                'fio_path': comp.get('fio_path'),
                'version': comp.get('version'),
                'action': 'compiled_and_installed',
                'logs': logs + comp.get('logs', []),
            }
        except Exception as e:
            log_cb('error', f'Auto-fix failed: {e}')
            return {'success': False, 'error': str(e), 'logs': logs}
