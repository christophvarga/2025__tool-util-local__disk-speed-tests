"""Mixin for FIO testing utilities: functionality tests, direct FIO execution,
QLab direct tests, and optimal path resolution.
"""

import json
import os
import subprocess
import time
from datetime import datetime
from typing import Dict, Any, Optional


class FioUtilsMixin:
    """FIO binary testing, direct execution, and QLab test patterns."""

    def test_fio_functionality(self):
        """Test FIO functionality from unsandboxed bridge server."""
        logs = []

        def log_cb(level, message):
            ts = datetime.now().strftime('%H:%M:%S')
            logs.append({'timestamp': ts, 'level': level, 'message': message})
            self.logger.info(f"[{level.upper()}] {message}")

        try:
            log_cb('info', 'Starting FIO functionality test from bridge server')
            log_cb('info',
                f'Process context: Unsandboxed bridge server (PID: {os.getpid()})')

            fio_path = self._find_fio_binary(log_cb)
            if not fio_path:
                return {'success': False, 'error': 'FIO binary not found', 'logs': logs}

            log_cb('info', f'Found FIO at: {fio_path}')
            test_file = '/tmp/fio_bridge_test_file'
            log_cb('info', f'Creating test file: {test_file}')
            with open(test_file, 'wb') as f:
                f.write(b'0' * (1024 * 1024))

            try:
                env = self._build_fio_env()
                fio_cmd = [
                    fio_path, '--name=bridge_test', f'--filename={test_file}',
                    '--size=1M', '--bs=4k', '--rw=read', '--runtime=3',
                    '--time_based=1', '--ioengine=sync', '--direct=0',
                    '--numjobs=1', '--group_reporting=1', '--output-format=json',
                    '--disable_lat=1', '--disable_clat=1', '--disable_slat=1',
                    '--disable_bw_measurement=1', '--minimal', '--thread',
                ]
                log_cb('info', f'Executing FIO: {" ".join(fio_cmd)}')

                result = subprocess.run(
                    fio_cmd, capture_output=True, text=True, timeout=30, env=env,
                )
                log_cb('info', f'FIO completed with rc: {result.returncode}')
                if result.stdout:
                    log_cb('info', f'FIO STDOUT: {result.stdout[:500]}...')
                if result.stderr:
                    log_cb('warning', f'FIO STDERR: {result.stderr}')

                if result.returncode == 0:
                    log_cb('info', 'FIO functionality test: PASSED')
                    return {
                        'success': True,
                        'message': 'FIO functionality test passed',
                        'fio_path': fio_path,
                        'test_output': result.stdout, 'logs': logs,
                    }
                elif 'failed to setup shm segment' in result.stderr:
                    log_cb('error', 'FIO failed: shared memory limitations')
                    return {
                        'success': False,
                        'error': 'FIO has shared memory limitations on macOS',
                        'fio_path': fio_path, 'fio_limited': True,
                        'stderr': result.stderr, 'logs': logs,
                    }
                else:
                    log_cb('error', f'FIO failed with rc {result.returncode}')
                    return {
                        'success': False,
                        'error': f'FIO test failed: {result.stderr}',
                        'fio_path': fio_path, 'logs': logs,
                    }
            finally:
                if os.path.exists(test_file):
                    os.remove(test_file)
                    log_cb('info', 'Test file cleaned up')
        except Exception as e:
            log_cb('error', f'FIO functionality test exception: {e}')
            return {'success': False, 'error': str(e), 'logs': logs}

    def run_direct_fio_test(self, test_params=None):
        """Run direct FIO test with macOS-safe parameters."""
        logs = []

        def log_cb(level, message):
            ts = datetime.now().strftime('%H:%M:%S')
            logs.append({'timestamp': ts, 'level': level, 'message': message})
            self.logger.info(f"[{level.upper()}] {message}")

        try:
            log_cb('info', 'Starting DIRECT FIO test from bridge server')
            log_cb('info',
                f'Process context: Unsandboxed bridge server (PID: {os.getpid()})')
            if test_params is None:
                test_params = {}

            test_size = test_params.get('size', '100M')
            test_type = test_params.get('rw', 'read')
            target_path = test_params.get('target_path', '/tmp')
            duration = test_params.get('duration', None)
            log_cb('info',
                f'Params: size={test_size}, rw={test_type}, target={target_path}')

            fio_path = self._find_fio_binary(log_cb)
            if not fio_path:
                return {'success': False, 'error': 'FIO binary not found', 'logs': logs}
            log_cb('info', f'Found FIO at: {fio_path}')

            if target_path.startswith('/dev/'):
                test_file = f'/tmp/direct_fio_test_{test_size}'
            else:
                test_file = f'{target_path}/direct_fio_test_{test_size}'
            log_cb('info', f'Test file: {test_file}')

            try:
                env = self._build_fio_env()
                fio_cmd = [
                    fio_path, '--name=direct_test', f'--filename={test_file}',
                    f'--size={test_size}', f'--rw={test_type}',
                    '--ioengine=posix', '--direct=0', '--output-format=json',
                ]
                if duration:
                    fio_cmd.extend([f'--runtime={duration}', '--time_based=1'])
                fio_cmd.extend(['--numjobs=1', '--group_reporting=1'])

                log_cb('info', f'Executing FIO: {" ".join(fio_cmd)}')
                start_time = time.time()
                result = subprocess.run(
                    fio_cmd, capture_output=True, text=True,
                    timeout=duration + 60 if duration else 120, env=env,
                )
                elapsed = time.time() - start_time
                log_cb('info', f'FIO completed in {elapsed:.2f}s, rc={result.returncode}')

                if result.returncode == 0:
                    fio_results = None
                    try:
                        fio_results = json.loads(result.stdout)
                    except json.JSONDecodeError as e:
                        log_cb('warning', f'Failed to parse FIO JSON: {e}')
                    return {
                        'success': True,
                        'message': 'Direct FIO test completed successfully',
                        'fio_path': fio_path, 'command': ' '.join(fio_cmd),
                        'elapsed_time': elapsed, 'raw_output': result.stdout,
                        'fio_results': fio_results,
                        'test_params': test_params, 'logs': logs,
                    }
                else:
                    log_cb('error', f'FIO failed with rc {result.returncode}')
                    return {
                        'success': False,
                        'error': f'FIO test failed with rc {result.returncode}',
                        'fio_path': fio_path, 'command': ' '.join(fio_cmd),
                        'stderr': result.stderr, 'stdout': result.stdout,
                        'elapsed_time': elapsed, 'logs': logs,
                    }
            finally:
                if os.path.exists(test_file):
                    try:
                        os.remove(test_file)
                        log_cb('info', 'Test file cleaned up')
                    except Exception as e:
                        log_cb('warning', f'Failed to cleanup test file: {e}')
        except subprocess.TimeoutExpired:
            msg = f'FIO test timed out after {duration + 60 if duration else 120}s'
            log_cb('error', msg)
            return {'success': False, 'error': msg, 'logs': logs}
        except Exception as e:
            log_cb('error', f'Direct FIO test exception: {e}')
            return {'success': False, 'error': str(e), 'logs': logs}

    def run_qlab_test_direct(self, test_params):
        """Run QLab-specific performance tests using direct FIO."""
        logs = []

        def log_cb(level, message):
            ts = datetime.now().strftime('%H:%M:%S')
            logs.append({'timestamp': ts, 'level': level, 'message': message})
            self.logger.info(f"[{level.upper()}] {message}")

        try:
            test_type = test_params.get('test_type', 'quick_max_speed')
            target_path = test_params.get('target_path', '/tmp')
            log_cb('info', f'Starting QLab test: {test_type}')

            presets = {
                'quick_max_speed': {'size': '500M', 'rw': 'randrw', 'duration': 180},
                'qlab_prores_422_show': {'size': '2G', 'rw': 'randrw', 'duration': 9900},
                'qlab_prores_hq_show': {'size': '4G', 'rw': 'randrw', 'duration': 9900},
            }
            if test_type not in presets:
                return {
                    'success': False,
                    'error': f'Unknown test type: {test_type}', 'logs': logs,
                }

            fio_params = {**presets[test_type], 'target_path': target_path}
            result = self.run_direct_fio_test(fio_params)
            if result['success'] and result.get('fio_results'):
                log_cb('info', 'Analyzing QLab performance metrics...')
            return result
        except Exception as e:
            log_cb('error', f'QLab test exception: {e}')
            return {'success': False, 'error': str(e), 'logs': logs}

    def get_optimal_fio_path(self):
        """Get the optimal FIO path, preferring the no-shm version."""
        candidates = [
            '/usr/local/bin/fio-nosmh',
            '/opt/homebrew/bin/fio',
            '/usr/local/bin/fio',
        ]
        for path in candidates:
            if os.path.exists(path) and os.access(path, os.X_OK):
                self.logger.info(f"Selected FIO: {path}")
                return path
        import shutil
        path = shutil.which('fio')
        if path:
            self.logger.info(f"Selected system FIO: {path}")
            return path
        self.logger.warning("No FIO binary found")
        return None

    # -----------------------------------------------------------------
    # Internal helper
    # -----------------------------------------------------------------
    @staticmethod
    def _find_fio_binary(log_cb=None):
        """Locate the best available fio binary."""
        import platform as _platform
        machine = _platform.machine().lower()
        arch_dir = 'arm64' if ('arm' in machine or 'aarch64' in machine) else 'x86_64'
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        for p in [
            os.path.join(repo_root, 'vendor', 'fio', 'macos', arch_dir, 'fio'),
            os.path.join(repo_root, 'vendor', 'fio', 'macos', arch_dir, 'fio-noshm'),
        ]:
            if os.path.exists(p) and os.access(p, os.X_OK):
                return p
        for p in ['/opt/homebrew/bin/fio', '/usr/local/bin/fio']:
            if os.path.exists(p) and os.access(p, os.X_OK):
                return p
        import shutil
        return shutil.which('fio')
