"""Mixin for subprocess execution, FIO config generation,
background test threads, and orphan-process cleanup.
"""
import json, os, subprocess, sys, tempfile, time
from datetime import datetime
from typing import Dict, Any, Optional, List


class ProcessManagerMixin:
    """Subprocess execution and FIO process lifecycle."""

    def execute_diskbench_command(self, args: List[str],
            estimated_duration: int = 0,
            log_callback: Optional[Any] = None) -> Dict[str, Any]:
        """Execute a diskbench command and return the result."""
        try:
            cmd = [sys.executable, 'main.py'] + args
            if estimated_duration > 0 and '--estimated-duration' not in args:
                cmd.extend(['--estimated-duration', str(estimated_duration)])
            cmd_str = ' '.join(cmd)
            if log_callback:
                log_callback('info', f"Executing command: {cmd_str}")
                log_callback('info', f"Working directory: {self.diskbench_path}")
                log_callback('info',
                    f"Process context: Unsandboxed bridge server (PID: {os.getpid()})")
            self.logger.debug(f"Executing: {cmd_str} in {self.diskbench_path}")
            env = self._build_fio_env()
            if log_callback:
                log_callback('info', "Environment: FIO_DISABLE_SHM=1, TMPDIR=/tmp")
            timeout_seconds = self._compute_timeout(args)
            result = subprocess.run(cmd, cwd=self.diskbench_path,
                capture_output=True, text=True, timeout=timeout_seconds, env=env)
            if log_callback:
                log_callback('info', f"Command rc: {result.returncode}")
                if result.stdout:
                    log_callback('stdout', f"STDOUT:\n{result.stdout}")
                if result.stderr:
                    log_callback('stderr', f"STDERR:\n{result.stderr}")
            self.logger.info(f"Command result: returncode={result.returncode}")
            if result.stdout:
                self.logger.info(f"STDOUT: {result.stdout}")
            if result.stderr:
                self.logger.info(f"STDERR: {result.stderr}")
            if result.returncode == 0:
                stdout_clean = self._extract_json_from_output(result.stdout)
                try:
                    return json.loads(stdout_clean)
                except json.JSONDecodeError:
                    return {'success': True, 'output': stdout_clean,
                            'stderr': result.stderr, 'command': cmd_str,
                            'returncode': result.returncode}
            else:
                return {'success': False, 'error': result.stderr or result.stdout,
                        'returncode': result.returncode, 'command': cmd_str}
        except subprocess.TimeoutExpired:
            error_msg = f'Command timed out after {timeout_seconds/3600:.1f}h: {cmd_str}'
            if log_callback:
                log_callback('error', error_msg)
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg, 'command': cmd_str}
        except Exception as e:
            error_msg = f'Command execution failed: {e}'
            if log_callback:
                log_callback('error', error_msg)
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg,
                    'command': cmd_str if 'cmd_str' in locals() else str(cmd)}

    # ----- helpers -----
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

    # ----- custom FIO config -----
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

    # ----- FIO orphan cleanup -----
    def cleanup_fio_processes(self, test_id: Optional[str] = None) -> List[int]:
        """Find and kill orphaned FIO processes related to our tests."""
        try:
            self.logger.info("Searching for orphaned FIO processes...")
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return []
            killed: List[int] = []
            markers = ('diskbench-test_', '/tmp/diskbench-', 'diskbench_', 'fio_config.ini')
            for line in result.stdout.split('\n'):
                if 'fio' not in line or not any(m in line for m in markers):
                    continue
                parts = line.split()
                if len(parts) < 2:
                    continue
                try:
                    pid = int(parts[1])
                except ValueError:
                    continue
                self.logger.info(f"Found orphaned FIO process: PID {pid}")
                try:
                    os.kill(pid, 15)
                    time.sleep(2)
                    try:
                        os.kill(pid, 0)
                        os.kill(pid, 9)
                    except ProcessLookupError:
                        pass
                    killed.append(pid)
                except ProcessLookupError:
                    pass
                except PermissionError:
                    self.logger.warning(f"Permission denied killing PID {pid}")
            if killed:
                self.logger.info(f"Cleaned up {len(killed)} orphaned FIO: {killed}")
            return killed
        except Exception as e:
            self.logger.error(f"Error cleaning up FIO processes: {e}")
            return []

    # ----- background test thread -----
    def _run_test_thread(self, test_id: str, args: List[str],
                         estimated_duration: int) -> None:
        """Run test in background thread with live progress monitoring."""
        process = None
        ti = self.running_tests[test_id]
        try:
            ti['status'] = 'running'
            ti['live_metrics'] = {}
            ti['current_phase'] = 'initializing'
            self.logger.info(f"Starting test {test_id}, est={estimated_duration}s")
            cmd = [sys.executable, 'main.py'] + args
            process = subprocess.Popen(
                cmd, cwd=self.diskbench_path, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True, env=self._build_fio_env(),
                start_new_session=True)
            self.running_processes[test_id] = process
            self.logger.info(f"Test {test_id} PID: {process.pid}")
            timeout_s = estimated_duration + 120
            try:
                stdout, stderr = process.communicate(timeout=timeout_s)
                if process.returncode == 0:
                    out_f = ti['output_file']
                    try:
                        if os.path.exists(out_f):
                            with open(out_f, 'r') as f:
                                ti['result'] = json.load(f)
                        else:
                            ti['result'] = {'success': True, 'output': stdout,
                                            'stderr': stderr, 'returncode': 0}
                    except Exception:
                        ti['result'] = {'success': True, 'output': stdout}
                    ti['status'] = 'completed'
                    ti['progress'] = 100
                    ti['current_phase'] = 'completed'
                    self._save_persistent_state()
                else:
                    ti['status'] = 'failed'
                    ti['error'] = stderr or stdout or 'Unknown error'
                    ti['current_phase'] = 'failed'
                    self.logger.error(f"Test {test_id} failed: {stderr}")
            except subprocess.TimeoutExpired:
                self.logger.warning(f"Test {test_id} timed out after {timeout_s}s")
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait()
                ti['status'] = 'timeout'
                ti['error'] = f'Test timed out after {timeout_s} seconds'
                ti['current_phase'] = 'timeout'
        except Exception as e:
            ti['status'] = 'failed'
            ti['error'] = str(e)
            ti['current_phase'] = 'failed'
            self.logger.error(f"Exception in test {test_id}: {e}")
            if process and process.poll() is None:
                try:
                    process.terminate(); process.wait(timeout=5)
                except Exception:
                    try:
                        process.kill(); process.wait()
                    except Exception:
                        pass
        finally:
            self.running_processes.pop(test_id, None)
            ti['end_time'] = datetime.now().isoformat()
            self.logger.info(f"Test {test_id} thread completed")
