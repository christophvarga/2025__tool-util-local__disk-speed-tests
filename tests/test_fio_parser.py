#!/usr/bin/env python3
"""
Unit tests for FIO JSON parsing functionality.

Tests the robustness of the FIO output parser against different
JSON schemas and format changes between FIO versions.
"""

import unittest
import json
import os
import sys
from pathlib import Path

# Add the diskbench directory to the path for imports
test_dir = Path(__file__).parent
diskbench_dir = test_dir.parent / "diskbench"
sys.path.insert(0, str(diskbench_dir))

from core.fio_runner import FioRunner


class TestFioParser(unittest.TestCase):
    """Test FIO JSON parsing with different format versions."""

    def setUp(self):
        """Set up test fixtures."""
        self.fio_runner = FioRunner()
        self.fixtures_dir = test_dir / "fixtures"
        
    def load_fixture(self, filename):
        """Load a JSON fixture file."""
        fixture_path = self.fixtures_dir / filename
        with open(fixture_path, 'r') as f:
            return json.load(f)
    
    def test_parse_current_fio_format(self):
        """Test parsing current FIO 3.40 format with both bw and bw_bytes."""
        fio_data = self.load_fixture("fio_3_40_output.json")
        
        # Test the _process_fio_results method
        processed = self.fio_runner._process_fio_results(fio_data)
        summary = processed['summary']
        
        # Verify IOPS parsing
        self.assertAlmostEqual(summary['total_read_iops'], 213.25, places=2)
        self.assertAlmostEqual(summary['total_write_iops'], 200.5, places=2)
        
        # Verify bandwidth parsing (should prefer 'bw' field when available)
        self.assertAlmostEqual(summary['total_read_bw'], 853.0, places=1)
        self.assertAlmostEqual(summary['total_write_bw'], 802.0, places=1)
        
        # Verify latency parsing (should be converted from ns to ms)
        self.assertAlmostEqual(summary['avg_read_latency'], 0.0209, places=4)  # 20900 ns -> 0.0209 ms
        self.assertAlmostEqual(summary['avg_write_latency'], 0.028, places=3)   # 28000 ns -> 0.028 ms
        
        # Verify runtime
        self.assertEqual(summary['total_runtime'], 60000)

    def test_parse_legacy_fio_format(self):
        """Test parsing legacy FIO format with only bw_bytes field."""
        fio_data = self.load_fixture("fio_legacy_output.json")
        
        # Test the _process_fio_results method
        processed = self.fio_runner._process_fio_results(fio_data)
        summary = processed['summary']
        
        # Verify IOPS parsing
        self.assertAlmostEqual(summary['total_read_iops'], 213.453125, places=2)
        self.assertAlmostEqual(summary['total_write_iops'], 196.875, places=2)
        
        # Verify bandwidth parsing (should fall back to bw_bytes / 1024)
        expected_read_bw = 873813 / 1024  # Convert bytes/s to KiB/s
        expected_write_bw = 803908 / 1024
        self.assertAlmostEqual(summary['total_read_bw'], expected_read_bw, places=1)
        self.assertAlmostEqual(summary['total_write_bw'], expected_write_bw, places=1)
        
        # Verify latency parsing (should be converted from ns to ms)
        self.assertAlmostEqual(summary['avg_read_latency'], 0.0162, places=4)  # 16200 ns -> 0.0162 ms
        self.assertAlmostEqual(summary['avg_write_latency'], 0.0225, places=4)   # 22500 ns -> 0.0225 ms
        
        # Verify runtime
        self.assertEqual(summary['total_runtime'], 30000)

    def test_parse_very_old_fio_format(self):
        """Test parsing very old FIO format (2.x) with minimal fields."""
        fio_data = self.load_fixture("fio_very_old_output.json")
        
        # Test the _process_fio_results method
        processed = self.fio_runner._process_fio_results(fio_data)
        summary = processed['summary']
        
        # Verify IOPS parsing
        self.assertAlmostEqual(summary['total_read_iops'], 128.0, places=1)
        self.assertAlmostEqual(summary['total_write_iops'], 102.0, places=1)
        
        # Verify bandwidth parsing (should fall back to bw_bytes / 1024)
        expected_read_bw = 524288 / 1024  # Convert bytes/s to KiB/s
        expected_write_bw = 419430 / 1024
        self.assertAlmostEqual(summary['total_read_bw'], expected_read_bw, places=1)
        self.assertAlmostEqual(summary['total_write_bw'], expected_write_bw, places=1)
        
        # Verify latency parsing (should be converted from ns to ms)
        self.assertAlmostEqual(summary['avg_read_latency'], 0.009, places=3)  # 9000 ns -> 0.009 ms
        self.assertAlmostEqual(summary['avg_write_latency'], 0.0115, places=4)   # 11500 ns -> 0.0115 ms
        
        # Verify runtime
        self.assertEqual(summary['total_runtime'], 20000)

    def test_bandwidth_fallback_logic(self):
        """Test bandwidth parsing fallback from bw to bw_bytes."""
        # Create test data with only bw_bytes field
        test_data = {
            "jobs": [{
                "read": {
                    "bw_bytes": 2097152,  # 2 MB/s
                    "iops": 512.0,
                    "lat_ns": {"mean": 15000.0}
                },
                "write": {
                    "bw_bytes": 1572864,  # 1.5 MB/s
                    "iops": 384.0,
                    "lat_ns": {"mean": 20000.0}
                },
                "job_runtime": 30000
            }]
        }
        
        processed = self.fio_runner._process_fio_results(test_data)
        summary = processed['summary']
        
        # Should convert bw_bytes to KiB/s: 2097152 bytes/s = 2048 KiB/s
        self.assertAlmostEqual(summary['total_read_bw'], 2048.0, places=1)
        self.assertAlmostEqual(summary['total_write_bw'], 1536.0, places=1)

    def test_bandwidth_preference_logic(self):
        """Test that bw field is preferred over bw_bytes when both are present."""
        # Create test data with both bw and bw_bytes fields
        test_data = {
            "jobs": [{
                "read": {
                    "bw": 1024,  # KiB/s - this should be preferred
                    "bw_bytes": 2097152,  # bytes/s - this should be ignored
                    "iops": 256.0,
                    "lat_ns": {"mean": 12000.0}
                },
                "write": {
                    "bw": 768,  # KiB/s - this should be preferred
                    "bw_bytes": 1572864,  # bytes/s - this should be ignored
                    "iops": 192.0,
                    "lat_ns": {"mean": 18000.0}
                },
                "job_runtime": 25000
            }]
        }
        
        processed = self.fio_runner._process_fio_results(test_data)
        summary = processed['summary']
        
        # Should use bw field directly
        self.assertAlmostEqual(summary['total_read_bw'], 1024.0, places=1)
        self.assertAlmostEqual(summary['total_write_bw'], 768.0, places=1)

    def test_missing_fields_handling(self):
        """Test handling of missing or zero fields gracefully."""
        # Create test data with missing or zero fields
        test_data = {
            "jobs": [{
                "read": {
                    "bw": 0,  # Zero bandwidth
                    "bw_bytes": 0,  # Zero bytes bandwidth
                    "iops": 0.0,
                    # Missing lat_ns field
                },
                "write": {
                    # Missing bw field
                    "bw_bytes": 1048576,  # Should fall back to this
                    "iops": 128.0,
                    "lat_ns": {"mean": 25000.0}
                },
                "job_runtime": 20000
            }]
        }
        
        processed = self.fio_runner._process_fio_results(test_data)
        summary = processed['summary']
        
        # Read should have zero bandwidth
        self.assertEqual(summary['total_read_bw'], 0.0)
        self.assertEqual(summary['total_read_iops'], 0.0)
        
        # Write should fall back to bw_bytes
        self.assertAlmostEqual(summary['total_write_bw'], 1024.0, places=1)  # 1048576 / 1024
        self.assertAlmostEqual(summary['total_write_iops'], 128.0, places=1)
        
        # Latency should handle missing read latency gracefully
        self.assertEqual(summary.get('avg_read_latency', 0), 0)
        self.assertAlmostEqual(summary['avg_write_latency'], 0.025, places=3)  # 25000 ns -> 0.025 ms

    def test_multiple_jobs_aggregation(self):
        """Test aggregation of metrics across multiple jobs."""
        test_data = {
            "jobs": [
                {
                    "read": {"bw": 500, "iops": 125.0, "lat_ns": {"mean": 10000.0}},
                    "write": {"bw": 400, "iops": 100.0, "lat_ns": {"mean": 15000.0}},
                    "job_runtime": 30000
                },
                {
                    "read": {"bw": 600, "iops": 150.0, "lat_ns": {"mean": 12000.0}},
                    "write": {"bw": 500, "iops": 125.0, "lat_ns": {"mean": 18000.0}},
                    "job_runtime": 25000
                }
            ]
        }
        
        processed = self.fio_runner._process_fio_results(test_data)
        summary = processed['summary']
        
        # Should aggregate across jobs
        self.assertAlmostEqual(summary['total_read_bw'], 1100.0, places=1)  # 500 + 600
        self.assertAlmostEqual(summary['total_write_bw'], 900.0, places=1)   # 400 + 500
        self.assertAlmostEqual(summary['total_read_iops'], 275.0, places=1)  # 125 + 150
        self.assertAlmostEqual(summary['total_write_iops'], 225.0, places=1) # 100 + 125
        
        # Latency should be averaged: read = (10000 + 12000) / 2 / 1_000_000
        self.assertAlmostEqual(summary['avg_read_latency'], 0.011, places=3)
        self.assertAlmostEqual(summary['avg_write_latency'], 0.0165, places=4)
        
        # Runtime should be the maximum
        self.assertEqual(summary['total_runtime'], 30000)

    def test_edge_case_empty_jobs(self):
        """Test handling of empty jobs array."""
        test_data = {"jobs": []}
        
        processed = self.fio_runner._process_fio_results(test_data)
        summary = processed['summary']
        
        # Should handle empty gracefully - summary will be empty dict for no jobs
        self.assertEqual(summary.get('total_read_iops', 0), 0)
        self.assertEqual(summary.get('total_write_iops', 0), 0)
        self.assertEqual(summary.get('total_read_bw', 0), 0)
        self.assertEqual(summary.get('total_write_bw', 0), 0)
        self.assertEqual(summary.get('total_runtime', 0), 0)

    def test_edge_case_malformed_job(self):
        """Test handling of malformed job data."""
        test_data = {
            "jobs": [{
                # Missing read/write sections
                "job_runtime": 15000
            }]
        }
        
        # Should not raise an exception
        processed = self.fio_runner._process_fio_results(test_data)
        summary = processed['summary']
        
        # Should handle missing sections gracefully
        self.assertEqual(summary['total_read_iops'], 0)
        self.assertEqual(summary['total_write_iops'], 0)
        self.assertEqual(summary['total_read_bw'], 0)
        self.assertEqual(summary['total_write_bw'], 0)
        self.assertEqual(summary['total_runtime'], 15000)

    def test_iops_mean_fallback(self):
        """Test fallback from iops to iops_mean for older FIO versions."""
        test_data = {
            "jobs": [{
                "read": {
                    "bw": 800,
                    "iops_mean": 200.0,  # Should fall back to this when iops missing
                    "lat_ns": {"mean": 12000.0}
                },
                "write": {
                    "bw": 600,
                    "iops": 150.0,  # This should be preferred over iops_mean
                    "iops_mean": 999.0,  # This should be ignored
                    "lat_ns": {"mean": 16000.0}
                },
                "job_runtime": 30000
            }]
        }
        
        processed = self.fio_runner._process_fio_results(test_data)
        summary = processed['summary']
        
        # Should use iops_mean for read (no iops field)
        self.assertAlmostEqual(summary['total_read_iops'], 200.0, places=1)
        
        # Should prefer iops over iops_mean for write
        self.assertAlmostEqual(summary['total_write_iops'], 150.0, places=1)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
