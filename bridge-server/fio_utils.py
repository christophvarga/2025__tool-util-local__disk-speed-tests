"""Mixin for FIO testing utilities: functionality tests, direct FIO execution,
QLab direct tests, config generation, and optimal path resolution."""

import json
import os
import subprocess
import tempfile
import time
from datetime import datetime
from typing import Dict, Any


class FioUtilsMixin:
    """FIO binary testing, direct execution, and QLab test patterns."""

    @staticmethod
    def _make_fio_logger(logs_list, logger):
        def log_cb(level, message):
            ts = datetime.now().strftime('%H:%M:%S')
            logs_list.append({'timestamp': ts, 'level': level, 'message': message})
            logger.info(f"[{level.upper()}] {message}")
        return log_cb

    def test_fio_functionality(self):
        """Test FIO functionality from unsandboxed bridge server."""
        logs = []
        log_cb = self._make_fio_logger(logs, self.logger)

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
        log_cb = self._make_fio_logger(logs, self.logger)

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
        log_cb = self._make_fio_logger(logs, self.logger)

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

    # ----- FIO environment & timeout helpers -----
    @staticmethod
    def _build_fio_env() -> dict:
        """Build an environment dict suitable for FIO execution."""
        env = os.environ.copy()
        env['FIO_DISABLE_SHM'] = '1'
        env['TMPDIR'] = '/tmp'
        machine = __import__('platform').machine().lower()
        arch_dir = 'arm64' if ('arm' in machine or 'aarch64' in machine) else 'x86_64'
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        vendor_path = os.path.join(repo_root, 'vendor', 'fio', 'macos', arch_dir)
        env['PATH'] = f"{vendor_path}:/opt/homebrew/bin:/usr/local/bin:{env.get('PATH', '')}"
        env['PYTHONPATH'] = repo_root
        return env

    @staticmethod
    def _compute_timeout(args: list) -> int:
        timeout = 300
        if '--test' in args:
            idx = args.index('--test')
            if idx + 1 < len(args):
                tt = args[idx + 1]
                if 'show' in tt:
                    timeout = 11000
                elif 'max_sustained' in tt:
                    timeout = 6000
        return timeout

    # ----- custom FIO config generation -----
    def _generate_custom_fio_config(self, params: Dict[str, Any]) -> str:
        """Generate a temporary FIO config file for custom tests."""
        _s = lambda v: str(v).replace('\n', '').replace('\r', '')
        duration = int(params.get('duration', 60))
        bs = _s(params.get('block_size', '1M'))
        rw_mix = int(params.get('rw_mix', 50))
        nj = int(params.get('numjobs', 4))
        iod = int(params.get('iodepth', 32))
        rate = _s(params.get('target_rate', ''))
        rw = 'read' if rw_mix == 100 else ('write' if rw_mix == 0 else 'randrw')
        cfg = (
            "[global]\nioengine=posixaio\ndirect=0\ntime_based=1\n"
            "group_reporting=1\nthread=1\nnorandommap=1\n"
            "randrepeat=0\nrandom_generator=tausworthe64\n"
            f"runtime={duration}\nlog_avg_msec=1000\n"
            "write_bw_log=custom_test_bw\nwrite_lat_log=custom_test_lat\n\n"
            f"[custom_test]\nfilename=${{TEST_FILE}}\nsize=${{TEST_SIZE}}\n"
            f"bs={bs}\nrw={rw}\n"
        )
        if rw == 'randrw':
            cfg += f"rwmixread={rw_mix}\n"
        cfg += f"numjobs={nj}\niodepth={iod}\n"
        if rate:
            cfg += f"rate={rate}\n"
        fd, fn = tempfile.mkstemp(suffix='.fio', prefix='diskbench_custom_')
        with os.fdopen(fd, 'w') as f:
            f.write(cfg)
        self.logger.info(f"Generated custom FIO config: {fn}")
        return fn
