"""DiskBenchBridge core: initialisation, state persistence, JSON extraction,
and simple delegating commands (list_disks, validate, version, etc.).
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from typing import Dict, Any, Optional


class DiskBenchBridgeCore:
    """Base class for the bridge between web GUI and diskbench."""

    def __init__(self) -> None:
        self.diskbench_path: str = os.path.join(os.path.dirname(__file__), '..', 'diskbench')
        self.running_tests: Dict[str, Any] = {}
        self.running_processes: Dict[str, subprocess.Popen] = {}
        self.logger: logging.Logger = logging.getLogger(__name__)
        self._fio_checked: Optional[Dict[str, str]] = None
        self.state_file: str = '.state/diskbench_bridge_state.json'

        self._load_persistent_state()
        self._discover_orphaned_processes()

    # -----------------------------------------------------------------
    # FIO binary verification
    # -----------------------------------------------------------------
    def _verify_fio(self) -> Dict[str, str]:
        """Locate fio binary (prefer vendored) and return {'path', 'version'}."""
        if self._fio_checked:
            return self._fio_checked
        import shutil
        import platform as _platform

        try:
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        except Exception:
            repo_root = os.getcwd()
        machine = _platform.machine().lower()
        arch_dir = 'arm64' if ('arm' in machine or 'aarch64' in machine) else 'x86_64'
        vendor_candidates = [
            os.path.join(repo_root, 'vendor', 'fio', 'macos', arch_dir, 'fio'),
            os.path.join(repo_root, 'vendor', 'fio', 'macos', arch_dir, 'fio-noshm'),
        ]
        fio_path = None
        for p in vendor_candidates:
            if os.path.exists(p) and os.access(p, os.X_OK):
                fio_path = p
                break
        if not fio_path:
            fio_path = shutil.which('fio')
        if not fio_path:
            raise OSError(
                'fio binary not found. Place it at vendor/fio/macos/<arch>/fio '
                'or install via Homebrew.'
            )
        try:
            version_out = subprocess.check_output(
                [fio_path, "--version"], text=True
            ).strip()
        except Exception:
            version_out = 'unknown'
        self._fio_checked = {'path': fio_path, 'version': version_out}
        return self._fio_checked

    # -----------------------------------------------------------------
    # Persistent state
    # -----------------------------------------------------------------
    def _load_persistent_state(self):
        """Load persistent test state from disk."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state_data = json.load(f)
                self.running_tests = state_data.get('running_tests', {})
                for test_id, test_info in self.running_tests.items():
                    if test_info.get('status') == 'running':
                        test_info['status'] = 'disconnected'
                        test_info['disconnected_time'] = datetime.now().isoformat()
                self.logger.info(
                    f"Loaded persistent state: {len(self.running_tests)} tests"
                )
                self._save_persistent_state()
            else:
                self.logger.info("No persistent state file found - starting fresh")
        except Exception as e:
            self.logger.error(f"Failed to load persistent state: {e}")
            self.running_tests = {}

    def _save_persistent_state(self):
        """Save current test state to disk."""
        try:
            state_data = {
                'running_tests': self.running_tests,
                'last_updated': datetime.now().isoformat(),
            }
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save persistent state: {e}")

    def _discover_orphaned_processes(self):
        """Discover and handle orphaned FIO processes on startup."""
        try:
            self.logger.info("Discovering orphaned processes on startup...")
            disconnected_tests = [
                tid for tid, info in self.running_tests.items()
                if info.get('status') == 'disconnected'
            ]
            if disconnected_tests:
                self.logger.warning(
                    f"Found {len(disconnected_tests)} disconnected tests: "
                    f"{disconnected_tests}"
                )
                orphaned_pids = self.cleanup_fio_processes()
                if orphaned_pids:
                    self.logger.info(
                        f"Cleaned up {len(orphaned_pids)} orphaned FIO processes"
                    )
                    for test_id in disconnected_tests:
                        self.running_tests[test_id]['status'] = 'stopped'
                        self.running_tests[test_id]['error'] = (
                            f'Process orphaned during server restart - cleaned up '
                            f'{len(orphaned_pids)} FIO processes'
                        )
                        self.running_tests[test_id]['end_time'] = (
                            datetime.now().isoformat()
                        )
                else:
                    for test_id in disconnected_tests:
                        self.running_tests[test_id]['status'] = 'unknown'
                        self.running_tests[test_id]['error'] = (
                            'Test status unknown after server restart'
                        )
                        self.running_tests[test_id]['end_time'] = (
                            datetime.now().isoformat()
                        )
                self._save_persistent_state()
            else:
                self.logger.info("No disconnected tests found")
        except Exception as e:
            self.logger.error(f"Error discovering orphaned processes: {e}")

    # -----------------------------------------------------------------
    # JSON extraction
    # -----------------------------------------------------------------
    def _extract_json_from_output(self, output: str) -> str:
        """Extract JSON from mixed output (logs + JSON)."""
        try:
            stripped = output.strip()
            if stripped.startswith('{') and stripped.endswith('}'):
                try:
                    json.loads(stripped)
                    return stripped
                except json.JSONDecodeError:
                    pass

            start_idx = output.find('{')
            end_idx = output.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                candidate = output[start_idx:end_idx + 1]
                try:
                    json.loads(candidate)
                    return candidate
                except json.JSONDecodeError:
                    pass

            lines = output.split('\n')
            json_lines = []
            brace_count = 0
            in_json = False
            for line in lines:
                if not in_json and '{' in line.strip():
                    brace_idx = line.find('{')
                    if brace_idx != -1:
                        in_json = True
                        line = line[brace_idx:]
                        brace_count = 0
                if in_json:
                    json_lines.append(line)
                    brace_count += line.count('{') - line.count('}')
                    if brace_count == 0:
                        candidate = '\n'.join(json_lines)
                        try:
                            json.loads(candidate)
                            return candidate
                        except json.JSONDecodeError:
                            pass
            return output
        except Exception as e:
            self.logger.warning(f"Failed to extract JSON from output: {e}")
            return output

    # -----------------------------------------------------------------
    # Simple delegating commands
    # -----------------------------------------------------------------
    def list_disks(self):
        """List available disks."""
        return self.execute_diskbench_command(['--list-disks', '--json'])

    def validate_system(self):
        """Validate system requirements."""
        return self.execute_diskbench_command(['--validate', '--json'])

    def get_version(self):
        """Get diskbench version."""
        return self.execute_diskbench_command(['--version'])

    def detect_system_status(self):
        """Detect system status and FIO availability."""
        return self.execute_diskbench_command(['--detect', '--json'])

    def install_fio(self):
        """Install or fix FIO for macOS."""
        logs = []

        def log_callback(level, message):
            timestamp = datetime.now().strftime('%H:%M:%S')
            logs.append({'timestamp': timestamp, 'level': level, 'message': message})
            self.logger.info(f"[{level.upper()}] {message}")

        result = self.execute_diskbench_command(['--install', '--json'], log_callback)
        if isinstance(result, dict):
            result['logs'] = logs
        else:
            result = {'success': False, 'error': 'Unknown result format', 'logs': logs}
        return result

    def validate_setup(self):
        """Run setup validation tests."""
        result = self.execute_diskbench_command(['--validate', '--json'])
        if result and result.get('checks'):
            tests = []
            for check_name, check_data in result['checks'].items():
                tests.append({
                    'name': check_name.replace('_', ' ').title(),
                    'passed': check_data.get('passed', False),
                    'result': check_data.get('message', 'Unknown'),
                })
            return {
                'success': True,
                'tests': tests,
                'overall_status': result.get('overall_status', 'unknown'),
            }
        elif result and result.get('success') is False:
            return result
        else:
            return {'success': False, 'error': 'Invalid validation result format'}
