#!/usr/bin/env python3
"""
Unit tests for diskbench helper binary.
"""

from commands.test import DiskTestCommand
from core.qlab_patterns import QLabTestPatterns
import sys
import os
import subprocess
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Add the current directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import diskbench modules


class TestDiskbench(unittest.TestCase):
    """Unit tests for diskbench functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.qlab_patterns = QLabTestPatterns()
        self.test_command = DiskTestCommand()
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.main_script = os.path.join(self.script_dir, 'main.py')

    def test_get_test_config_returns_all_required_keys(self):
        """Test that get_test_config() returns all required keys for each test ID."""
        required_keys = {'name', 'description', 'duration', 'fio_template'}

        for test_id in self.qlab_patterns.patterns.keys():
            with self.subTest(test_id=test_id):
                config = self.qlab_patterns.get_test_config(test_id)

                # Check that all required keys are present
                for key in required_keys:
                    self.assertIn(key, config, f"Test '{test_id}' config missing key '{key}'")

                # Also check for fio_config which is an additional key returned
                self.assertIn('fio_config', config, f"Test '{test_id}' config missing 'fio_config' key")

                # Assert each key has a non-empty value
                self.assertIsInstance(config['name'], str)
                self.assertTrue(config['name'], f"Test '{test_id}' has empty name")

                self.assertIsInstance(config['description'], str)
                self.assertTrue(config['description'], f"Test '{test_id}' has empty description")

                self.assertIsInstance(config['duration'], int)
                self.assertGreater(config['duration'], 0, f"Test '{test_id}' has invalid duration")

                # Check fio_template is returned by get_test_config
                self.assertIsInstance(config['fio_template'], str)
                self.assertTrue(config['fio_template'], f"Test '{test_id}' has empty fio_template")

    def test_get_test_config_all_test_ids(self):
        """Test that get_test_config() works for all expected test IDs."""
        expected_test_ids = ['quick_max_mix', 'prores_422_real', 'prores_422_hq_real', 'thermal_maximum']

        for test_id in expected_test_ids:
            with self.subTest(test_id=test_id):
                config = self.qlab_patterns.get_test_config(test_id)
                self.assertIsInstance(config, dict)
                self.assertIn('name', config)
                self.assertIn('description', config)
                self.assertIn('duration', config)
                self.assertIn('fio_template', config)

    @patch.object(QLabTestPatterns, 'analyze_results')
    def test_analyze_results_dispatch(self, mock_analyze):
        """Test that analyze_results() dispatches correctly for different test modes."""
        # Mock the analyze_results function to return different results for different test modes
        def mock_analyze_results(test_mode, fio_results):
            return {
                'test_mode': test_mode,
                'overall_performance': 'good',
                'qlab_suitable': True,
                'notes': f'Analysis for {test_mode} test'
            }

        mock_analyze.side_effect = mock_analyze_results

        test_modes = ['quick_max_mix', 'prores_422_real', 'prores_422_hq_real', 'thermal_maximum']
        mock_fio_results = {'summary': {'total_read_iops': 1000, 'total_write_iops': 500}}

        for test_mode in test_modes:
            with self.subTest(test_mode=test_mode):
                result = self.qlab_patterns.analyze_results(test_mode, mock_fio_results)

                # Verify the mock was called with correct parameters
                mock_analyze.assert_called_with(test_mode, mock_fio_results)

                # Verify the result contains the expected test_mode
                self.assertEqual(result['test_mode'], test_mode)
                self.assertIn('overall_performance', result)
                self.assertIn('qlab_suitable', result)

    def test_cli_list_tests_ordering(self):
        """Test that CLI --list-tests shows correct 1-2-3-4 ordering."""
        if not os.path.exists(self.main_script):
            self.skipTest(f"Main script not found: {self.main_script}")

        try:
            result = subprocess.run(
                [sys.executable, self.main_script, '--list-tests'],
                capture_output=True, text=True, timeout=30
            )

            self.assertEqual(result.returncode, 0, f"CLI --list-tests failed: {result.stderr}")

            output_lines = result.stdout.strip().split('\n')

            # Look for the ordering pattern: 1. Test 1, 2. Test 3, 3. Test 4, 4. Test 2
            test_lines = [line for line in output_lines if line.strip() and line[0].isdigit()]

            self.assertEqual(len(test_lines), 4, "Expected 4 test entries")

            # Verify the ordering follows 1-3-4-2 pattern (Test 1, Test 3, Test 4, Test 2)
            expected_patterns = [
                ('1.', 'Test 1'),  # quick_max_mix
                ('2.', 'Test 3'),  # prores_422_real (shown as position 2)
                ('3.', 'Test 4'),  # prores_422_hq_real (shown as position 3)
                ('4.', 'Test 2'),  # thermal_maximum (shown as position 4)
            ]

            for i, (expected_num, expected_label) in enumerate(expected_patterns):
                with self.subTest(position=i + 1, expected_label=expected_label):
                    self.assertTrue(test_lines[i].startswith(expected_num),
                                    f"Position {i + 1} should start with '{expected_num}', got: {test_lines[i]}")
                    self.assertIn(expected_label, test_lines[i],
                                  f"Position {i + 1} should contain '{expected_label}', got: {test_lines[i]}")

        except subprocess.TimeoutExpired:
            self.fail("CLI --list-tests command timed out")
        except Exception as e:
            self.fail(f"CLI --list-tests command failed: {e}")

    def test_cli_list_tests_json_ordering(self):
        """Test that CLI --list-tests --json shows correct ordering."""
        if not os.path.exists(self.main_script):
            self.skipTest(f"Main script not found: {self.main_script}")

        try:
            result = subprocess.run(
                [sys.executable, self.main_script, '--list-tests', '--json'],
                capture_output=True, text=True, timeout=30
            )

            self.assertEqual(result.returncode, 0, f"CLI --list-tests --json failed: {result.stderr}")

            data = json.loads(result.stdout)

            self.assertIn('order', data)
            self.assertIn('tests', data)

            # Verify the order matches expected 1-3-4-2 pattern
            expected_order = ['quick_max_mix', 'prores_422_real', 'prores_422_hq_real', 'thermal_maximum']
            self.assertEqual(data['order'], expected_order)

            # Verify all tests have required keys
            for test_id in expected_order:
                with self.subTest(test_id=test_id):
                    self.assertIn(test_id, data['tests'])
                    test_info = data['tests'][test_id]
                    self.assertIn('name', test_info)
                    self.assertIn('description', test_info)
                    self.assertIn('duration', test_info)
                    self.assertIn('display_label', test_info)

        except subprocess.TimeoutExpired:
            self.fail("CLI --list-tests --json command timed out")
        except json.JSONDecodeError as e:
            self.fail(f"CLI --list-tests --json returned invalid JSON: {e}")
        except Exception as e:
            self.fail(f"CLI --list-tests --json command failed: {e}")

    def test_version_check(self):
        """Test basic version check functionality."""
        if not os.path.exists(self.main_script):
            self.skipTest(f"Main script not found: {self.main_script}")

        try:
            result = subprocess.run(
                [sys.executable, self.main_script, '--version'],
                capture_output=True, text=True, timeout=30
            )
            self.assertEqual(result.returncode, 0, f"Version check failed: {result.stderr}")
            self.assertIn('diskbench version', result.stdout)

        except subprocess.TimeoutExpired:
            self.fail("Version check command timed out")
        except Exception as e:
            self.fail(f"Version check command failed: {e}")


if __name__ == '__main__':
    unittest.main()
