"""
QLab test patterns dictionary for diskbench.
"""

# Dictionary of QLab test templates keyed by test identifier
QLAB_PATTERNS = {
    'quick_max_mix': {
        'name': 'Quick Max Mix Test',
        'description': 'Fast mixed workload test to determine maximum performance',
        'duration': 300,  # 5 minutes
        'fio_template': """
[global]
ioengine=posixaio
direct=0
runtime=300
time_based=1
thread=1
log_avg_msec=1000
write_bw_log=quick_max_mix_bw
write_lat_log=quick_max_mix_lat

[quick_max_mix]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=4M
rw=randrw
rwmixread=70
numjobs=4
iodepth=32
"""
    },

    'prores_422_real': {
        'name': 'ProRes 422 Real-World Test',
        'description': 'Realistic ProRes 422 playback simulation with multiple streams',
        'duration': 1800,  # 30 minutes
        'fio_template': """
[global]
ioengine=posixaio
direct=0
time_based=1
group_reporting=1
thread=1
norandommap=1
randrepeat=0
random_generator=tausworthe64
log_avg_msec=1000
write_bw_log=prores_422_real_bw
write_lat_log=prores_422_real_lat
lat_percentiles=1

[prores_422_warmup]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=1M,64K,4K
rw=randrw
rwmixread=95
numjobs=2
runtime=600
rate=200M,25M
ioengine=posixaio
iodepth=16
direct=0

[prores_422_playback]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=1M,256K,16K
rw=randrw
rwmixread=98
numjobs=4
runtime=1200
rate=500M,50M
rate_process=poisson
ioengine=posixaio
iodepth=24
direct=0
thinktime=8000000
thinktime_spin=2000000
startdelay=600
"""
    },

    'prores_422_hq_real': {
        'name': 'ProRes 422 HQ Real-World Test',
        'description': 'Realistic ProRes 422 HQ playback simulation with higher bandwidth',
        'duration': 1800,  # 30 minutes
        'fio_template': """
[global]
ioengine=posixaio
direct=0
time_based=1
group_reporting=1
thread=1
norandommap=1
randrepeat=0
random_generator=tausworthe64
log_avg_msec=1000
write_bw_log=prores_422_hq_real_bw
write_lat_log=prores_422_hq_real_lat
lat_percentiles=1

[prores_422_hq_warmup]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=2M,128K,8K
rw=randrw
rwmixread=95
numjobs=2
runtime=600
rate=400M,50M
ioengine=posixaio
iodepth=24
direct=0

[prores_422_hq_playback]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=2M,512K,32K
rw=randrw
rwmixread=98
numjobs=6
runtime=1200
rate=1000M,100M
rate_process=poisson
ioengine=posixaio
iodepth=32
direct=0
thinktime=6000000
thinktime_spin=1500000
startdelay=600
"""
    },

    'thermal_maximum': {
        'name': 'Thermal Maximum Test',
        'description': 'Extended high-load test to identify thermal throttling and maximum sustained performance',
        'duration': 3600,  # 60 minutes
        'fio_template': """
[global]
ioengine=posixaio
direct=0
time_based=1
group_reporting=1
thread=1
log_avg_msec=1000
write_bw_log=thermal_max_bw
write_lat_log=thermal_max_lat
lat_percentiles=1

[thermal_ramp_up]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=8M
rw=read
numjobs=2
runtime=600
rate=500M
iodepth=32

[thermal_sustained_low]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=8M
rw=randrw
rwmixread=80
numjobs=4
runtime=900
rate=1000M
iodepth=48
startdelay=600

[thermal_sustained_high]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=4M
rw=randrw
rwmixread=75
numjobs=8
runtime=1200
rate=2000M
iodepth=64
startdelay=1500

[thermal_maximum]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=2M
rw=randrw
rwmixread=70
numjobs=12
runtime=900
rate=3000M
iodepth=96
startdelay=2700
"""
    }
}


class QLabTestPatterns:
    """Class for managing QLab test patterns and configurations."""

    def __init__(self):
        self.patterns = QLAB_PATTERNS

        # Test display order: 1-3-4-2 corresponds to quick → prores422 → prores422hq → thermal
        self.test_display_order = [
            'quick_max_mix',      # Test 1
            'prores_422_real',    # Test 3 (shown as position 2)
            'prores_422_hq_real',  # Test 4 (shown as position 3)
            'thermal_maximum'     # Test 2 (shown as position 4)
        ]

        # Map test IDs to display labels
        self.test_display_labels = {
            'quick_max_mix': 'Test 1',
            'prores_422_real': 'Test 3',
            'prores_422_hq_real': 'Test 4',
            'thermal_maximum': 'Test 2'
        }

    def get_test_config(self, test_id: str, disk_path: str = None, test_size_gb: int = None) -> dict:
        """
        Get test configuration metadata for a given test ID.

        Args:
            test_id: The test pattern identifier
            disk_path: Target disk path (optional, for compatibility)
            test_size_gb: Test size in GB (optional, for compatibility)

        Returns:
            Dictionary containing test metadata including name, description, duration, and fio_config

        Raises:
            KeyError: If test_id is not found, with friendly error message listing valid IDs
        """
        if test_id not in self.patterns:
            valid_ids = ', '.join(sorted(self.patterns.keys()))
            raise KeyError(
                f"Test ID '{test_id}' not found. Valid test IDs are: {valid_ids}"
            )

        pattern = self.patterns[test_id]

        # Create the configuration dict with metadata
        config = {
            'name': pattern['name'],
            'description': pattern['description'],
            'duration': pattern['duration'],
            'fio_template': pattern['fio_template'],
            'fio_config': pattern['fio_template']
        }

        # If disk_path and test_size_gb are provided, process the template
        if disk_path and test_size_gb:
            # Create test file path
            if disk_path.startswith('/dev/'):
                test_file = f'/tmp/diskbench_test_{test_id}.dat'
            elif disk_path.startswith('/Volumes/'):
                test_file = f'{disk_path}/diskbench_test_{test_id}.dat'
            else:
                test_file = f'{disk_path}/diskbench_test_{test_id}.dat'

            # Process template variables
            processed_config = pattern['fio_template']
            processed_config = processed_config.replace('${TEST_FILE}', test_file)
            processed_config = processed_config.replace('${TEST_SIZE}', f'{test_size_gb}G')

            config['fio_config'] = processed_config

        return config

    def get_ordered_tests(self) -> list:
        """
        Get test IDs in display order (1-3-4-2: quick → prores422 → prores422hq → thermal).

        Returns:
            List of test IDs in the order they should be displayed to users
        """
        return self.test_display_order.copy()

    def get_test_display_label(self, test_id: str) -> str:
        """
        Get the user-visible display label for a test ID.

        Args:
            test_id: The test pattern identifier

        Returns:
            Display label (e.g., "Test 1", "Test 3") or the test_id if not found
        """
        return self.test_display_labels.get(test_id, test_id)

    def analyze_results(self, test_mode: str, fio_results: dict) -> dict:
        """
        Analyze FIO results for QLab-specific metrics.

        Args:
            test_mode: The test mode that was run
            fio_results: Raw FIO results

        Returns:
            Dictionary containing QLab-specific analysis
        """
        # Placeholder implementation - would need actual analysis logic
        return {
            'overall_performance': 'good',
            'qlab_suitable': True,
            'recommended_streams': 4,
            'notes': f'Analysis for {test_mode} test'
        }
