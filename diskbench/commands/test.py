"""
Test command for diskbench helper binary.
"""

import logging
import os
import tempfile
import warnings
from typing import Dict, Any, Optional, List
from datetime import datetime

from diskbench.core.fio_runner import FioRunner
from diskbench.core.qlab_patterns import QLabTestPatterns
from diskbench.utils.security import validate_disk_path, get_safe_test_directory, check_available_space
from diskbench.utils.system_info import get_system_info

logger = logging.getLogger(__name__)


class DiskTestCommand:
    """Command to execute disk performance tests."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.fio_runner = FioRunner()
        self.qlab_patterns = QLabTestPatterns()

        # Backward compatibility mapping from old test IDs to new ones
        self.deprecated_test_mapping = {
            'quick_max_speed': 'quick_max_mix',
            'qlab_prores_422_show': 'prores_422_real',
            'qlab_prores_hq_show': 'prores_422_hq_real',
            'max_sustained': 'thermal_maximum'
        }

    def stop_test(self):
        """Stop the currently running FIO test."""
        return self.fio_runner.stop_fio_test()

    def execute_builtin_test(self, disk_path: str, test_mode: str, test_size_gb: int,
                             output_file: str, show_progress: bool = False,
                             json_output: bool = False, estimated_duration: int = 0) -> Optional[Dict[str, Any]]:
        """
        Execute a built-in test pattern.

        Args:
            disk_path: Target disk path
            test_mode: Test mode (setup_check, qlab_prores_422, etc.)
            test_size_gb: Test file size in GB
            output_file: Output file path
            show_progress: Whether to show progress
            json_output: Whether to format as JSON

        Returns:
            Test results or None on error
        """
        try:
            # Handle deprecated test IDs with backward compatibility
            original_test_mode = test_mode
            if test_mode in self.deprecated_test_mapping:
                new_test_mode = self.deprecated_test_mapping[test_mode]
                self.logger.warning(f"Test ID '{test_mode}' is deprecated. Please use '{new_test_mode}' instead.")
                warnings.warn(
                    f"Test ID '{test_mode}' is deprecated and will be removed in a future version. "
                    f"Use '{new_test_mode}' instead.",
                    DeprecationWarning,
                    stacklevel=2
                )
                test_mode = new_test_mode

            # Validate inputs
            if not validate_disk_path(disk_path):
                self.logger.error(f"Invalid disk path: {disk_path}")
                return None

            if not check_available_space(disk_path, test_size_gb + 1):  # +1GB buffer
                self.logger.error(f"Insufficient space on {disk_path}")
                return None

            # Get test configuration
            try:
                config = self.qlab_patterns.get_test_config(test_mode, disk_path, test_size_gb)
            except KeyError as e:
                # KeyError already contains the user-friendly error message
                self.logger.error(str(e))
                return None

            # Create test directory
            base_path = self._get_test_base_path(disk_path)
            test_directory = get_safe_test_directory(base_path, test_mode)

            self.logger.info(f"Running {test_mode} test on {disk_path}")
            self.logger.info(f"Test directory: {test_directory}")

            # Print test directory for bridge server to capture
            if show_progress:
                print(f"TEST_DIR:{test_directory}")

            # Progress callback
            progress_callback = None
            if show_progress:
                progress_callback = self._progress_callback

            # Get estimated duration from config
            estimated_duration = config.get('duration', 0)  # Default to 0 if not found

            # Run FIO test
            fio_results = self.fio_runner.run_fio_test(
                config['fio_config'],
                test_directory,
                estimated_duration,  # Pass estimated duration
                progress_callback
            )

            # Check for FIO test failure - both None and error dictionary
            if not fio_results:
                self.logger.error("FIO test failed - no results returned")
                return None

            # Check if FIO returned an error dictionary instead of results
            if isinstance(fio_results, dict) and 'error' in fio_results:
                self.logger.error(f"FIO test failed with error: {fio_results['error']}")
                self.logger.error(f"FIO stderr: {fio_results.get('fio_stderr', 'No stderr')}")
                self.logger.error(f"FIO stdout: {fio_results.get('fio_stdout', 'No stdout')}")
                return None

            # Analyze results for QLab
            qlab_analysis = self.qlab_patterns.analyze_results(test_mode, fio_results)

            # Compile final results
            test_info = {
                'test_mode': test_mode,
                'test_name': config['name'],
                'description': config['description'],
                'disk_path': disk_path,
                'test_size_gb': test_size_gb,
                'timestamp': datetime.now().isoformat(),
                'test_directory': test_directory
            }

            # Include original test mode if it was deprecated and mapped
            if original_test_mode != test_mode:
                test_info['original_test_mode'] = original_test_mode
                test_info['deprecated_mapping'] = True

            results = {
                'test_info': test_info,
                'system_info': get_system_info(),
                'fio_results': fio_results,
                'qlab_analysis': qlab_analysis,
                'recommendations': self._generate_recommendations(qlab_analysis)
            }

            return results

        except Exception as e:
            self.logger.error(f"Error executing builtin test: {e}")
            return None

    def execute_custom_test(self, disk_path: str, config_file: str, test_size_gb: int,
                            output_file: str, show_progress: bool = False,
                            json_output: bool = False, estimated_duration: int = 0) -> Optional[Dict[str, Any]]:
        """
        Execute a custom FIO configuration test.

        Args:
            disk_path: Target disk path
            config_file: Path to custom FIO config file
            test_size_gb: Test file size in GB
            output_file: Output file path
            show_progress: Whether to show progress
            json_output: Whether to format as JSON

        Returns:
            Test results or None on error
        """
        try:
            # Validate inputs
            if not validate_disk_path(disk_path):
                self.logger.error(f"Invalid disk path: {disk_path}")
                return None

            if not os.path.exists(config_file):
                self.logger.error(f"Config file not found: {config_file}")
                return None

            if not check_available_space(disk_path, test_size_gb + 1):
                self.logger.error(f"Insufficient space on {disk_path}")
                return None

            # Read custom config
            with open(config_file, 'r') as f:
                config_content = f.read()

            # Process config to inject disk path and size
            processed_config = self._process_custom_config(
                config_content, disk_path, test_size_gb
            )

            # Create test directory
            base_path = self._get_test_base_path(disk_path)
            test_directory = get_safe_test_directory(base_path, 'custom_test')

            self.logger.info(f"Running custom test on {disk_path}")
            self.logger.info(f"Config file: {config_file}")
            self.logger.info(f"Test directory: {test_directory}")

            # Progress callback
            progress_callback = None
            if show_progress:
                progress_callback = self._progress_callback

            # Get estimated duration for custom tests (if available in config)
            # For custom tests, we might not have a predefined duration, so we'll pass 0
            # or try to parse it from the config if a specific field is used.
            # For now, we'll assume 0 for custom tests unless specified otherwise.
            estimated_duration = 0

            # Run FIO test
            fio_results = self.fio_runner.run_fio_test(
                processed_config,
                test_directory,
                estimated_duration,  # Pass estimated duration
                progress_callback
            )

            if not fio_results:
                self.logger.error("FIO test failed")
                return None

            # Basic analysis (no QLab-specific analysis for custom tests)
            basic_analysis = self._basic_analysis(fio_results)

            # Compile final results
            results = {
                'test_info': {
                    'test_mode': 'custom',
                    'test_name': 'Custom FIO Test',
                    'description': f'Custom test from {config_file}',
                    'disk_path': disk_path,
                    'test_size_gb': test_size_gb,
                    'timestamp': datetime.now().isoformat(),
                    'test_directory': test_directory,
                    'config_file': config_file
                },
                'system_info': get_system_info(),
                'fio_results': fio_results,
                'analysis': basic_analysis,
                'recommendations': self._generate_basic_recommendations(basic_analysis)
            }

            return results

        except Exception as e:
            self.logger.error(f"Error executing custom test: {e}")
            return None

    def _get_test_base_path(self, disk_path: str) -> str:
        """Get base path for test files."""
        if disk_path.startswith('/dev/'):
            # For raw devices, use /tmp
            return '/tmp'
        elif disk_path.startswith('/Volumes/'):
            # For mounted volumes, use the volume
            return disk_path
        else:
            # For other paths, use the path itself
            return disk_path

    def _process_custom_config(self, config_content: str, disk_path: str,
                               test_size_gb: int) -> str:
        """Process custom config to inject disk path and size."""
        # Replace placeholders in config
        processed = config_content

        # Common replacements
        replacements = {
            '${DISK_PATH}': disk_path,
            '${TEST_SIZE}': f'{test_size_gb}G',
            '${TEST_SIZE_MB}': str(test_size_gb * 1024),
            '${TEST_SIZE_KB}': str(test_size_gb * 1024 * 1024)
        }

        for placeholder, value in replacements.items():
            processed = processed.replace(placeholder, value)

        return processed

    def _progress_callback(self, progress_info: Dict[str, Any]):
        """Handle progress updates."""
        progress = progress_info.get('progress', 0)
        elapsed = progress_info.get('elapsed_time', 0)
        status = progress_info.get('status', 'running')

        print(f"\rProgress: {progress:.1f}% | Elapsed: {elapsed:.1f}s | Status: {status}", end='', flush=True)

        if status == 'completed':
            print()  # New line when completed

    def _basic_analysis(self, fio_results: Dict[str, Any]) -> Dict[str, Any]:
        """Perform basic analysis of FIO results."""
        summary = fio_results.get('summary', {})

        analysis = {
            'performance_class': 'unknown',
            'read_performance': 'unknown',
            'write_performance': 'unknown',
            'latency_performance': 'unknown',
            'overall_score': 0
        }

        # Classify read performance
        read_iops = summary.get('total_read_iops', 0)
        if read_iops > 50000:
            analysis['read_performance'] = 'excellent'
        elif read_iops > 20000:
            analysis['read_performance'] = 'good'
        elif read_iops > 5000:
            analysis['read_performance'] = 'fair'
        else:
            analysis['read_performance'] = 'poor'

        # Classify write performance
        write_iops = summary.get('total_write_iops', 0)
        if write_iops > 40000:
            analysis['write_performance'] = 'excellent'
        elif write_iops > 15000:
            analysis['write_performance'] = 'good'
        elif write_iops > 3000:
            analysis['write_performance'] = 'fair'
        else:
            analysis['write_performance'] = 'poor'

        # Classify latency performance
        avg_latency = (summary.get('avg_read_latency', 0) + summary.get('avg_write_latency', 0)) / 2
        if avg_latency < 1:
            analysis['latency_performance'] = 'excellent'
        elif avg_latency < 5:
            analysis['latency_performance'] = 'good'
        elif avg_latency < 20:
            analysis['latency_performance'] = 'fair'
        else:
            analysis['latency_performance'] = 'poor'

        # Overall performance class
        performance_scores = {
            'excellent': 4,
            'good': 3,
            'fair': 2,
            'poor': 1,
            'unknown': 0
        }

        total_score = (performance_scores[analysis['read_performance']] +
                       performance_scores[analysis['write_performance']] +
                       performance_scores[analysis['latency_performance']])

        analysis['overall_score'] = total_score

        if total_score >= 10:
            analysis['performance_class'] = 'excellent'
        elif total_score >= 7:
            analysis['performance_class'] = 'good'
        elif total_score >= 4:
            analysis['performance_class'] = 'fair'
        else:
            analysis['performance_class'] = 'poor'

        return analysis

    def _generate_recommendations(self, qlab_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on QLab analysis."""
        recommendations = []

        overall = qlab_analysis.get('overall_performance', 'unknown')

        if overall == 'excellent':
            recommendations.extend([
                "✅ Excellent performance for QLab",
                "✅ Suitable for complex shows with multiple video layers",
                "✅ Can handle rapid cue triggering",
                "✅ Good for 4K video content"
            ])
        elif overall == 'good':
            recommendations.extend([
                "✅ Good performance for most QLab applications",
                "✅ Suitable for standard video playback",
                "⚠️ May struggle with very complex shows",
                "💡 Consider SSD upgrade for demanding applications"
            ])
        elif overall == 'fair':
            recommendations.extend([
                "⚠️ Fair performance - basic QLab usage only",
                "⚠️ Pre-load cues when possible",
                "⚠️ Avoid rapid cue sequences",
                "💡 SSD upgrade recommended"
            ])
        else:
            recommendations.extend([
                "❌ Poor performance for QLab",
                "❌ May experience dropouts and delays",
                "❌ Not suitable for live performance",
                "🔧 SSD upgrade strongly recommended"
            ])

        return recommendations

    def _generate_basic_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate basic recommendations."""
        recommendations = []

        performance_class = analysis.get('performance_class', 'unknown')

        if performance_class == 'excellent':
            recommendations.append("✅ Excellent disk performance")
        elif performance_class == 'good':
            recommendations.append("✅ Good disk performance")
        elif performance_class == 'fair':
            recommendations.append("⚠️ Fair disk performance - consider upgrade")
        else:
            recommendations.append("❌ Poor disk performance - upgrade recommended")

        return recommendations
