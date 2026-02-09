"""Mixin for starting, stopping, and managing disk performance tests."""
import os, signal, sys, tempfile, threading, time
from datetime import datetime
from typing import Dict, Any, List
from validation import _validate_custom_fio_params, _sanitize_error


class TestControlMixin:
    """Start / stop / stop-all logic for disk performance tests."""

    def start_test(self, test_params: Dict[str, Any]) -> Dict[str, Any]:
        """Start a disk performance test with single-instance enforcement."""
        try:
            self._verify_fio()
        except OSError as e:
            return {'success': False, 'error': str(e)}

        try:
            # Look up security validators from the server module so that
            # monkeypatch in tests (which patches bridge.validate_disk_path
            # etc.) takes effect.
            _srv = sys.modules.get('server')
            if _srv:
                _validate_path = getattr(_srv, 'validate_disk_path')
                _is_sys = getattr(_srv, 'is_system_path')
                _check_space = getattr(_srv, 'check_available_space')
            else:
                from validation import (
                    validate_disk_path as _validate_path,
                    is_system_path as _is_sys,
                    check_available_space as _check_space,
                )

            disk_path = test_params.get('disk_path', '/tmp')
            if not _validate_path(disk_path):
                return {
                    'success': False,
                    'error': f'Invalid or inaccessible disk path: {disk_path}',
                }
            if _is_sys(disk_path):
                return {
                    'success': False,
                    'error': f'Refusing to test on system path: {disk_path}',
                }
            size_gb = float(test_params.get('size_gb', 1))
            if not _check_space(disk_path, size_gb):
                return {
                    'success': False,
                    'error': (
                        f'Insufficient disk space at {disk_path} '
                        f'for {size_gb} GB test'
                    ),
                }

            running_ids = [
                tid for tid, info in self.running_tests.items()
                if info.get('status') == 'running'
            ]
            if running_ids:
                return {
                    'success': False,
                    'error': (
                        f'Test already running (ID: {running_ids[0]}). '
                        'Stop current test before starting a new one.'
                    ),
                }

            requested = test_params.get('test_type', 'quick_max_speed')
            mapping = {
                'quick_max_speed': 'quick_max_mix',
                'qlab_prores_422_show': 'prores_422_real',
                'qlab_prores_hq_show': 'prores_422_hq_real',
                'thermal_maximum_analyser': 'thermal_maximum',
            }

            from diskbench.core.qlab_patterns import QLabTestPatterns
            qlab_patterns = QLabTestPatterns()

            diskbench_test_type = None
            custom_config_file = None
            estimated_duration = 60

            if requested == 'custom':
                custom_params = test_params.get('custom_params', {})
                try:
                    _validate_custom_fio_params(custom_params)
                except ValueError as e:
                    return {
                        'success': False,
                        'error': f"Invalid custom test parameter: {e}",
                    }
                try:
                    custom_config_file = self._generate_custom_fio_config(
                        custom_params
                    )
                    estimated_duration = int(custom_params.get('duration', 60))
                    diskbench_test_type = 'custom'
                except Exception as e:
                    self.logger.error(f"Custom config generation failed: {e}")
                    return {
                        'success': False,
                        'error': "Failed to generate custom config",
                    }
            elif requested in mapping:
                diskbench_test_type = mapping[requested]
            elif requested in qlab_patterns.patterns:
                diskbench_test_type = requested
            else:
                valid = sorted(
                    list(mapping.keys())
                    + list(qlab_patterns.patterns.keys())
                    + ['custom']
                )
                valid_str = "', '".join(valid)
                return {
                    'success': False,
                    'error': (
                        f"Unknown test id '{requested}'. "
                        f"Valid choices: '{valid_str}'"
                    ),
                }

            test_id = f"test_{int(time.time())}"
            args: List[str] = []
            if diskbench_test_type == 'custom' and custom_config_file:
                args.extend(['--custom-config', custom_config_file])
            else:
                args.extend(['--test', diskbench_test_type])
            args.extend(['--disk', disk_path, '--size', str(size_gb), '--json'])

            fd, output_file = tempfile.mkstemp(
                suffix='.json', prefix=f'diskbench-{test_id}-',
            )
            os.close(fd)
            args.extend(['--output', output_file])
            if test_params.get('show_progress', True):
                args.append('--progress')
            args.append('--verbose')

            if diskbench_test_type != 'custom':
                dur_map = {
                    'quick_max_speed': 60,
                    'qlab_prores_422_show': 9300,
                    'qlab_prores_hq_show': 9300,
                    'thermal_maximum': 5400,
                }
                estimated_duration = dur_map.get(diskbench_test_type, 60)

            self.running_tests[test_id] = {
                'status': 'starting',
                'start_time': datetime.now().isoformat(),
                'params': test_params,
                'output_file': output_file,
                'progress': 0,
                'diskbench_test_type': diskbench_test_type,
                'estimated_duration': estimated_duration,
            }

            thread = threading.Thread(
                target=self._run_test_thread,
                args=(test_id, args, estimated_duration),
            )
            thread.daemon = True
            thread.start()

            return {
                'success': True,
                'test_id': test_id,
                'status': 'started',
                'diskbench_test_type': diskbench_test_type,
                'estimated_duration': estimated_duration,
            }
        except Exception as e:
            self.logger.error(f"start_test failed: {e}")
            return {'success': False, 'error': _sanitize_error(e)}

    def stop_test(self, test_id: str) -> Dict[str, Any]:
        """Stop a running test and cleanup processes."""
        try:
            if test_id not in self.running_tests:
                return {'success': False, 'error': 'Test not found'}
            test_info = self.running_tests[test_id]
            if test_info.get('status') not in ['running', 'starting']:
                return {
                    'success': False,
                    'error': (
                        f'Test is not running '
                        f'(status: {test_info.get("status")})'
                    ),
                }

            process_killed = False
            if test_id in self.running_processes:
                process = self.running_processes[test_id]
                self.logger.info(
                    f"Stopping test {test_id} "
                    f"(PID: {process.pid}, PGID: {os.getpgid(process.pid)})"
                )
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    time.sleep(2)
                    os.killpg(os.getpgid(process.pid), 0)
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    self.logger.info(
                        f"Force-killed process group for test {test_id}"
                    )
                    process_killed = True
                except (ProcessLookupError, OSError):
                    self.logger.info(
                        f"Process group for test {test_id} terminated gracefully."
                    )
                    process_killed = True
                except Exception as e:
                    self.logger.error(
                        f"Error stopping process group for {test_id}: {e}"
                    )
                del self.running_processes[test_id]

            self.logger.info(f"Running FIO cleanup for test {test_id}...")
            killed_pids = self.cleanup_fio_processes(test_id)

            self.running_tests[test_id]['status'] = 'stopped'
            self.running_tests[test_id]['end_time'] = datetime.now().isoformat()
            self.running_tests[test_id]['error'] = 'Test stopped by user'

            parts = [f'Test {test_id}']
            if process_killed:
                parts.append('stopped successfully. Killed tracked process')
            else:
                parts.append('marked as stopped')
            if killed_pids:
                parts.append(f'and {len(killed_pids)} orphaned FIO processes')
            return {'success': True, 'message': '. '.join(parts) + '.',
                    'killed_pids': killed_pids}
        except Exception as e:
            self.logger.error(f"Exception stopping test {test_id}: {e}")
            return {'success': False, 'error': str(e)}

    def stop_all_tests(self) -> Dict[str, Any]:
        """Stop all running tests and cleanup processes."""
        try:
            running_ids = [
                tid for tid, info in self.running_tests.items()
                if info.get('status') == 'running'
            ]
            if not running_ids:
                self.logger.info(
                    "No tracked running tests, checking for orphaned FIO..."
                )
                killed_pids = self.cleanup_fio_processes()
                if killed_pids:
                    return {
                        'success': True,
                        'message': (
                            f'No tracked tests running, but cleaned up '
                            f'{len(killed_pids)} orphaned FIO processes'
                        ),
                        'stopped_tests': [],
                        'killed_pids': killed_pids,
                    }
                return {
                    'success': True,
                    'message': 'No running tests to stop',
                    'stopped_tests': [],
                }

            stopped_tests = []
            errors = []
            total_killed: List[int] = []
            for test_id in running_ids:
                result = self.stop_test(test_id)
                if result.get('success'):
                    stopped_tests.append(test_id)
                    if result.get('killed_pids'):
                        total_killed.extend(result['killed_pids'])
                else:
                    errors.append(f"Test {test_id}: {result.get('error')}")

            final_killed = self.cleanup_fio_processes()
            total_killed.extend(final_killed)

            if errors:
                return {
                    'success': False,
                    'error': f'Some tests failed to stop: {"; ".join(errors)}',
                    'stopped_tests': stopped_tests,
                    'killed_pids': total_killed,
                }
            message = f'Successfully stopped {len(stopped_tests)} tests'
            if total_killed:
                message += f' and cleaned up {len(total_killed)} FIO processes'
            return {
                'success': True,
                'message': message,
                'stopped_tests': stopped_tests,
                'killed_pids': total_killed,
            }
        except Exception as e:
            self.logger.error(f"Exception stopping all tests: {e}")
            return {'success': False, 'error': str(e)}
