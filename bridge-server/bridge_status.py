"""Mixin for background-test management and test-status queries,
including live metrics and QLab performance analysis.
"""

from datetime import datetime
from typing import Dict, Any


class BridgeStatusMixin:
    """Methods for querying and managing test status."""

    def get_background_tests_status(self) -> Dict[str, Any]:
        """Get status of all background/disconnected tests."""
        try:
            background_tests = []
            for test_id, test_info in self.running_tests.items():
                if test_info.get('status') in ['disconnected', 'unknown']:
                    background_tests.append({
                        'test_id': test_id,
                        'status': test_info.get('status'),
                        'start_time': test_info.get('start_time'),
                        'disconnected_time': test_info.get('disconnected_time'),
                        'test_type': test_info.get('diskbench_test_type'),
                        'disk_path': test_info.get('params', {}).get('disk_path'),
                        'error': test_info.get('error'),
                    })
            return {
                'success': True,
                'background_tests': background_tests,
                'count': len(background_tests),
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def cleanup_background_test(self, test_id: str) -> Dict[str, Any]:
        """Clean up a specific background/disconnected test."""
        try:
            if test_id not in self.running_tests:
                return {'success': False, 'error': 'Test not found'}
            test_info = self.running_tests[test_id]
            if test_info.get('status') not in ['disconnected', 'unknown']:
                return {
                    'success': False,
                    'error': (
                        f'Test is not in background state '
                        f'(status: {test_info.get("status")})'
                    ),
                }
            killed_pids = self.cleanup_fio_processes(test_id)
            del self.running_tests[test_id]
            self._save_persistent_state()
            message = f'Background test {test_id} cleaned up'
            if killed_pids:
                message += f' (killed {len(killed_pids)} FIO processes)'
            return {
                'success': True,
                'message': message,
                'killed_pids': killed_pids,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def cleanup_all_background_tests(self) -> Dict[str, Any]:
        """Clean up all background/disconnected tests."""
        try:
            background_test_ids = [
                tid for tid, info in self.running_tests.items()
                if info.get('status') in ['disconnected', 'unknown']
            ]
            if not background_test_ids:
                return {
                    'success': True,
                    'message': 'No background tests to clean up',
                    'cleaned_tests': [],
                }
            cleaned_tests = []
            total_killed_pids = []
            for test_id in background_test_ids:
                result = self.cleanup_background_test(test_id)
                if result.get('success'):
                    cleaned_tests.append(test_id)
                    if result.get('killed_pids'):
                        total_killed_pids.extend(result['killed_pids'])
            final_killed_pids = self.cleanup_fio_processes()
            total_killed_pids.extend(final_killed_pids)
            message = f'Cleaned up {len(cleaned_tests)} background tests'
            if total_killed_pids:
                message += f' and {len(total_killed_pids)} FIO processes'
            return {
                'success': True,
                'message': message,
                'cleaned_tests': cleaned_tests,
                'killed_pids': total_killed_pids,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # -----------------------------------------------------------------
    # Test status
    # -----------------------------------------------------------------
    def get_current_test(self):
        """Get the currently running or disconnected test, if any."""
        for test_id, test_info in self.running_tests.items():
            if test_info.get('status') in ['running', 'disconnected']:
                return {
                    'success': True,
                    'test_running': True,
                    'test_info': self.get_test_status(test_id).get('test_info'),
                }
        return {'success': True, 'test_running': False}

    def get_test_status(self, test_id):
        """Get enhanced status of a running test with QLab metrics."""
        if test_id not in self.running_tests:
            return {'success': False, 'error': 'Test not found'}

        test_info = self.running_tests[test_id].copy()
        if test_info['status'] == 'running':
            elapsed = (
                datetime.now()
                - datetime.fromisoformat(test_info['start_time'])
            ).total_seconds()
            test_type = test_info.get('diskbench_test_type', 'quick_max_speed')
            estimated_duration = self._estimate_duration(test_type)
            progress = min(95, (elapsed / estimated_duration) * 100)
            remaining_time = max(0, estimated_duration - elapsed)
            test_info.update({
                'progress': progress,
                'elapsed_time': elapsed,
                'remaining_time': remaining_time,
                'estimated_duration': estimated_duration,
                'live_metrics': self._get_live_test_metrics(
                    test_id, test_type, elapsed
                ),
                'qlab_analysis': self._get_qlab_performance_analysis(
                    test_id, test_type, elapsed
                ),
            })
        return {'success': True, 'test_info': test_info}

    @staticmethod
    def _estimate_duration(test_type: str) -> int:
        durations = {
            'qlab_prores_422_show': 9300,
            'qlab_prores_hq_show': 9300,
            'thermal_maximum': 5400,
            'quick_max_speed': 60,
        }
        return durations.get(test_type, 60)

    def _get_live_test_metrics(self, test_id, test_type, elapsed):
        """Get live performance metrics with status messages."""
        if test_type == 'quick_max_speed':
            return {
                'status': 'measuring_max_read_speed',
                'message': f'Quick Max Speed Test ({elapsed:.0f}s)',
                'description': 'Maximum sequential read speed measurement',
                'phase': 'Single continuous read test',
                'elapsed_time': elapsed,
                'test_type': test_type,
            }
        elif 'show' in test_type:
            if elapsed < 1800:
                phase, description = "Show Preparation", "Media preload and setup"
            elif elapsed < 7200:
                phase = "Normal Show Operation"
                description = "1x4K + 3xHD ProRes continuous playback"
            else:
                phase = "Show Finale"
                description = "Intensive crossfades and maximum load"
            codec = "422" if "422" in test_type else "HQ"
            return {
                'status': 'running_show_pattern',
                'message': f'{phase} ({elapsed // 60:.0f}m {elapsed % 60:.0f}s)',
                'description': f'ProRes {codec} show pattern - {description}',
                'phase': phase,
                'elapsed_time': elapsed,
                'test_type': test_type,
            }
        elif test_type == 'thermal_maximum':
            return {
                'status': 'thermal_endurance_test',
                'message': (
                    f'Thermal Maximum Test '
                    f'({elapsed // 60:.0f}m {elapsed % 60:.0f}s)'
                ),
                'description': 'Maximum sustained load for thermal testing',
                'phase': 'Continuous maximum performance',
                'elapsed_time': elapsed,
                'test_type': test_type,
            }
        return {
            'status': 'running_test',
            'message': f'Running Test ({elapsed:.0f}s)',
            'description': f'Performance test: {test_type}',
            'phase': 'Test in progress',
            'elapsed_time': elapsed,
            'test_type': test_type,
        }

    def _get_qlab_performance_analysis(self, test_id, test_type, elapsed):
        """Generate QLab-specific performance analysis."""
        qlab_requirements = {
            'prores_422_real': {'min_throughput': 350, 'name': 'ProRes 422'},
            'prores_422_hq_real': {'min_throughput': 700, 'name': 'ProRes HQ'},
            'quick_max_mix': {'min_throughput': 300, 'name': 'Basic'},
            'thermal_maximum': {'min_throughput': 400, 'name': 'Thermal Maximum'},
        }
        requirement = qlab_requirements.get(
            test_type, qlab_requirements['quick_max_mix']
        )
        return {
            'status': 'pending',
            'status_message': 'Waiting for real test data',
            'requirement_name': requirement['name'],
            'min_required_mbps': requirement['min_throughput'],
            'current_margin_percent': 0,
            'min_margin_percent': 0,
            'consistency_score': 100,
            'stutters': 0,
            'dropouts': 0,
            'show_ready': False,
            'note': 'Real performance analysis will be available from FIO test results',
        }
