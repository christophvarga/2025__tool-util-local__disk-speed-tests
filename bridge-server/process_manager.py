"""Mixin for subprocess execution, background test threads,
and orphan-process cleanup.
"""
import json, os, subprocess, sys, time
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

    # ----- FIO orphan cleanup -----
    def cleanup_fio_processes(self, test_id: Optional[str] = None) -> List[int]:
        """Terminate FIO processes using PID tracking (primary) with
        ``ps aux`` pattern matching as a fallback for true orphans.

        Args:
            test_id: If given, only clean up the process tracked for that
                     test.  If ``None``, sweep *all* tracked processes and
                     then fall back to ``ps aux`` for untracked orphans.

        Returns:
            List of PIDs that were successfully killed.
        """
        killed: List[int] = []
        try:
            # --- Primary: PID-based cleanup via self.running_processes ---
            if test_id is not None:
                # Targeted cleanup for a single test
                process = self.running_processes.get(test_id)
                if process is not None:
                    killed.extend(self._kill_tracked_process(test_id, process))
            else:
                # General sweep: iterate all tracked processes
                for tid in list(self.running_processes):
                    proc = self.running_processes.get(tid)
                    if proc is not None:
                        killed.extend(self._kill_tracked_process(tid, proc))

                # --- Fallback: ps aux pattern matching for true orphans ---
                orphan_pids = self._find_orphan_fio_pids()
                for pid in orphan_pids:
                    if pid in killed:
                        continue
                    killed.extend(self._kill_pid(pid, label="orphaned FIO"))

            if killed:
                self.logger.info(
                    f"Cleaned up {len(killed)} FIO process(es): {killed}"
                )
            return killed
        except Exception as e:
            self.logger.error(f"Error cleaning up FIO processes: {e}")
            return killed

    # ----- kill helpers -----
    def _kill_tracked_process(self, test_id: str,
                              process: subprocess.Popen) -> List[int]:
        """Terminate a tracked subprocess.Popen and remove it from the
        registry.  Returns a list containing the PID if it was killed."""
        pid = process.pid
        result: List[int] = []
        try:
            # Check whether the process is still alive
            os.kill(pid, 0)
        except ProcessLookupError:
            self.logger.info(
                f"Tracked process for {test_id} (PID {pid}) already exited"
            )
            self.running_processes.pop(test_id, None)
            return result
        except PermissionError:
            # Process exists but we cannot signal it
            self.logger.warning(
                f"Permission denied checking PID {pid} for {test_id}"
            )
            self.running_processes.pop(test_id, None)
            return result

        self.logger.info(f"Killing tracked process for {test_id} (PID {pid})")
        result = self._kill_pid(pid, label=f"tracked[{test_id}]")
        self.running_processes.pop(test_id, None)
        return result

    @staticmethod
    def _pid_alive(pid: int) -> bool:
        """Return True if *pid* is still running."""
        try:
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, PermissionError):
            return False

    def _kill_pid(self, pid: int, label: str = "FIO") -> List[int]:
        """Send SIGTERM, wait briefly, escalate to SIGKILL if needed.
        Returns ``[pid]`` on success or ``[]`` on failure."""
        try:
            os.kill(pid, 15)  # SIGTERM
            time.sleep(2)
            if self._pid_alive(pid):
                os.kill(pid, 9)  # SIGKILL
                self.logger.info(f"Force-killed {label} PID {pid}")
            else:
                self.logger.info(f"Terminated {label} PID {pid} gracefully")
            return [pid]
        except ProcessLookupError:
            self.logger.info(f"{label} PID {pid} already exited")
            return []
        except PermissionError:
            self.logger.warning(f"Permission denied killing {label} PID {pid}")
            return []

    def _find_orphan_fio_pids(self) -> List[int]:
        """Use ``ps aux`` as a fallback to discover FIO processes that are
        not tracked in ``self.running_processes``."""
        tracked_pids = {
            p.pid for p in self.running_processes.values()
            if p is not None
        }
        try:
            result = subprocess.run(
                ['ps', 'aux'], capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0:
                return []
        except Exception as e:
            self.logger.error(f"ps aux fallback failed: {e}")
            return []

        markers = (
            'diskbench-test_', '/tmp/diskbench-', 'diskbench_', 'fio_config.ini',
        )
        orphans: List[int] = []
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
            if pid in tracked_pids:
                continue  # will be handled via primary path
            self.logger.info(f"Found untracked orphan FIO process: PID {pid}")
            orphans.append(pid)
        return orphans

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
