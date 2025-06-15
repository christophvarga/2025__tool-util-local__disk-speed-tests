"""
QLab-specific test patterns and analysis for diskbench helper binary.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class QLabTestPatterns:
    """Manages QLab-specific test patterns and result analysis."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.test_patterns = self._initialize_patterns()
    
    def _initialize_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize QLab test patterns."""
        return {
            'setup_check': {
                'name': 'QLab Setup Check',
                'description': 'Quick system validation for QLab compatibility',
                'duration': 30,
                'fio_template': self._get_setup_check_config()
            },
            'qlab_prores_422': {
                'name': 'QLab ProRes 422 Test',
                'description': 'Test pattern optimized for ProRes 422 video playback',
                'duration': 60,
                'fio_template': self._get_prores_422_config()
            },
            'qlab_prores_hq': {
                'name': 'QLab ProRes HQ Test',
                'description': 'Test pattern optimized for ProRes HQ video playback',
                'duration': 90,
                'fio_template': self._get_prores_hq_config()
            },
            'baseline_streaming': {
                'name': 'Baseline Streaming Test',
                'description': 'Basic streaming performance test for audio/video content',
                'duration': 45,
                'fio_template': self._get_baseline_streaming_config()
            }
        }
    
    def get_test_config(self, test_mode: str, disk_path: str, test_size_gb: int) -> Optional[Dict[str, Any]]:
        """
        Get test configuration for a specific mode.
        
        Args:
            test_mode: Test mode identifier
            disk_path: Target disk path
            test_size_gb: Test file size in GB
        
        Returns:
            Test configuration or None if not found
        """
        if test_mode not in self.test_patterns:
            return None
        
        pattern = self.test_patterns[test_mode]
        
        # Generate FIO config from template
        fio_config = self._generate_fio_config(
            pattern['fio_template'],
            disk_path,
            test_size_gb
        )
        
        return {
            'name': pattern['name'],
            'description': pattern['description'],
            'duration': pattern['duration'],
            'fio_config': fio_config
        }
    
    def analyze_results(self, test_mode: str, fio_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze FIO results for QLab-specific performance metrics.
        
        Args:
            test_mode: Test mode that was executed
            fio_results: Raw FIO results
        
        Returns:
            QLab-specific analysis
        """
        if test_mode not in self.test_patterns:
            return {'error': f'Unknown test mode: {test_mode}'}
        
        summary = fio_results.get('summary', {})
        
        # Base analysis
        analysis = {
            'test_mode': test_mode,
            'overall_performance': 'unknown',
            'video_playback_capability': 'unknown',
            'audio_cue_performance': 'unknown',
            'rapid_triggering_capability': 'unknown',
            'recommendations': [],
            'performance_scores': {}
        }
        
        # Mode-specific analysis
        if test_mode == 'setup_check':
            analysis.update(self._analyze_setup_check(summary))
        elif test_mode == 'qlab_prores_422':
            analysis.update(self._analyze_prores_422(summary))
        elif test_mode == 'qlab_prores_hq':
            analysis.update(self._analyze_prores_hq(summary))
        elif test_mode == 'baseline_streaming':
            analysis.update(self._analyze_baseline_streaming(summary))
        
        return analysis
    
    def _generate_fio_config(self, template: str, disk_path: str, test_size_gb: int) -> str:
        """Generate FIO config from template with substitutions."""
        config = template
        
        # Determine test file path
        if disk_path.startswith('/dev/'):
            # For raw devices, create test file in /tmp
            test_file = f'/tmp/qlab_test_file_{test_size_gb}G'
        else:
            # For mounted volumes, create test file on the volume
            test_file = f'{disk_path}/qlab_test_file_{test_size_gb}G'
        
        # Substitutions
        substitutions = {
            '${TEST_FILE}': test_file,
            '${TEST_SIZE}': f'{test_size_gb}G',
            '${TEST_SIZE_MB}': str(test_size_gb * 1024),
            '${DISK_PATH}': disk_path
        }
        
        for placeholder, value in substitutions.items():
            config = config.replace(placeholder, value)
        
        return config
    
    def _get_setup_check_config(self) -> str:
        """Get FIO config for setup check test."""
        return """
[global]
ioengine=sync
direct=0
ramp_time=5
runtime=30
time_based=1
group_reporting=1
thread=1

[setup_seq_read]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=1M
rw=read
numjobs=1
iodepth=1

[setup_seq_write]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=1M
rw=write
numjobs=1
iodepth=1

[setup_rand_read]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=4k
rw=randread
numjobs=1
iodepth=2
"""
    
    def _get_prores_422_config(self) -> str:
        """Get FIO config for ProRes 422 test."""
        return """
[global]
ioengine=sync
direct=0
ramp_time=10
runtime=60
time_based=1
group_reporting=1
thread=1

[prores422_sequential]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=1M
rw=read
numjobs=1
iodepth=1

[prores422_mixed_load]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=64k
rw=randrw
rwmixread=80
numjobs=1
iodepth=4

[prores422_burst_read]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=2M
rw=read
numjobs=1
iodepth=1
rate=220M
"""
    
    def _get_prores_hq_config(self) -> str:
        """Get FIO config for ProRes HQ test."""
        return """
[global]
ioengine=sync
direct=0
ramp_time=15
runtime=90
time_based=1
group_reporting=1
thread=1

[prores_hq_sequential]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=2M
rw=read
numjobs=1
iodepth=1

[prores_hq_sustained]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=1M
rw=read
numjobs=1
iodepth=2
rate=440M

[prores_hq_mixed]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=128k
rw=randrw
rwmixread=85
numjobs=1
iodepth=8

[prores_hq_burst]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=4M
rw=read
numjobs=1
iodepth=1
rate=600M
"""
    
    def _get_baseline_streaming_config(self) -> str:
        """Get FIO config for baseline streaming test."""
        return """
[global]
ioengine=sync
direct=0
ramp_time=5
runtime=45
time_based=1
group_reporting=1
thread=1

[streaming_sequential]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=512k
rw=read
numjobs=1
iodepth=1

[streaming_audio_cues]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=16k
rw=randread
numjobs=1
iodepth=1

[streaming_mixed]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=64k
rw=randrw
rwmixread=90
numjobs=1
iodepth=2
"""
    
    def _analyze_setup_check(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze setup check results."""
        read_bw = summary.get('total_read_bw', 0)  # KB/s
        write_bw = summary.get('total_write_bw', 0)  # KB/s
        read_iops = summary.get('total_read_iops', 0)
        avg_latency = summary.get('avg_read_latency', 0)
        
        # Convert to MB/s for easier analysis
        read_mb_s = read_bw / 1024
        write_mb_s = write_bw / 1024
        
        analysis = {}
        
        # Overall performance assessment
        if read_mb_s > 200 and write_mb_s > 150 and read_iops > 5000:
            analysis['overall_performance'] = 'excellent'
        elif read_mb_s > 100 and write_mb_s > 80 and read_iops > 2000:
            analysis['overall_performance'] = 'good'
        elif read_mb_s > 50 and write_mb_s > 40 and read_iops > 500:
            analysis['overall_performance'] = 'fair'
        else:
            analysis['overall_performance'] = 'poor'
        
        # QLab-specific assessments
        analysis['video_playback_capability'] = 'good' if read_mb_s > 100 else 'limited'
        analysis['audio_cue_performance'] = 'good' if read_iops > 1000 else 'limited'
        analysis['rapid_triggering_capability'] = 'good' if avg_latency < 10 else 'limited'
        
        analysis['performance_scores'] = {
            'read_bandwidth_mb_s': read_mb_s,
            'write_bandwidth_mb_s': write_mb_s,
            'read_iops': read_iops,
            'avg_latency_ms': avg_latency
        }
        
        return analysis
    
    def _analyze_prores_422(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze ProRes 422 test results."""
        read_bw = summary.get('total_read_bw', 0) / 1024  # Convert to MB/s
        read_iops = summary.get('total_read_iops', 0)
        avg_latency = summary.get('avg_read_latency', 0)
        
        analysis = {}
        
        # ProRes 422 requires ~220 MB/s sustained
        if read_bw > 300:
            analysis['overall_performance'] = 'excellent'
            analysis['video_playback_capability'] = 'multiple_streams'
        elif read_bw > 220:
            analysis['overall_performance'] = 'good'
            analysis['video_playback_capability'] = 'single_stream_reliable'
        elif read_bw > 150:
            analysis['overall_performance'] = 'fair'
            analysis['video_playback_capability'] = 'single_stream_marginal'
        else:
            analysis['overall_performance'] = 'poor'
            analysis['video_playback_capability'] = 'unreliable'
        
        analysis['audio_cue_performance'] = 'excellent' if read_iops > 3000 else 'good'
        analysis['rapid_triggering_capability'] = 'excellent' if avg_latency < 5 else 'good'
        
        analysis['performance_scores'] = {
            'sustained_read_mb_s': read_bw,
            'prores_422_capability': 'yes' if read_bw > 220 else 'no',
            'multiple_streams': 'yes' if read_bw > 440 else 'no'
        }
        
        return analysis
    
    def _analyze_prores_hq(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze ProRes HQ test results."""
        read_bw = summary.get('total_read_bw', 0) / 1024  # Convert to MB/s
        read_iops = summary.get('total_read_iops', 0)
        avg_latency = summary.get('avg_read_latency', 0)
        
        analysis = {}
        
        # ProRes HQ requires ~440 MB/s sustained
        if read_bw > 600:
            analysis['overall_performance'] = 'excellent'
            analysis['video_playback_capability'] = 'multiple_hq_streams'
        elif read_bw > 440:
            analysis['overall_performance'] = 'good'
            analysis['video_playback_capability'] = 'single_hq_stream_reliable'
        elif read_bw > 300:
            analysis['overall_performance'] = 'fair'
            analysis['video_playback_capability'] = 'hq_stream_marginal'
        else:
            analysis['overall_performance'] = 'poor'
            analysis['video_playback_capability'] = 'hq_not_recommended'
        
        analysis['audio_cue_performance'] = 'excellent' if read_iops > 5000 else 'good'
        analysis['rapid_triggering_capability'] = 'excellent' if avg_latency < 3 else 'good'
        
        analysis['performance_scores'] = {
            'sustained_read_mb_s': read_bw,
            'prores_hq_capability': 'yes' if read_bw > 440 else 'no',
            'multiple_hq_streams': 'yes' if read_bw > 880 else 'no'
        }
        
        return analysis
    
    def _analyze_baseline_streaming(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze baseline streaming test results."""
        read_bw = summary.get('total_read_bw', 0) / 1024  # Convert to MB/s
        read_iops = summary.get('total_read_iops', 0)
        avg_latency = summary.get('avg_read_latency', 0)
        
        analysis = {}
        
        # Basic streaming requirements
        if read_bw > 150 and read_iops > 2000:
            analysis['overall_performance'] = 'excellent'
        elif read_bw > 80 and read_iops > 1000:
            analysis['overall_performance'] = 'good'
        elif read_bw > 40 and read_iops > 500:
            analysis['overall_performance'] = 'fair'
        else:
            analysis['overall_performance'] = 'poor'
        
        # Streaming-specific assessments
        analysis['video_playback_capability'] = 'hd_capable' if read_bw > 50 else 'sd_only'
        analysis['audio_cue_performance'] = 'excellent' if read_iops > 1500 else 'good'
        analysis['rapid_triggering_capability'] = 'excellent' if avg_latency < 8 else 'fair'
        
        analysis['performance_scores'] = {
            'streaming_bandwidth_mb_s': read_bw,
            'audio_cue_iops': read_iops,
            'response_latency_ms': avg_latency
        }
        
        return analysis
