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
        """Initialize realistic QLab test patterns."""
        return {
            'quick_max_speed': {
                'name': 'Quick Max Speed Test',
                'description': 'Maximum read speed test in 3 minutes (continuous single job)',
                'duration': 180,  # 3 minutes
                'fio_template': self._get_quick_max_speed_config()
            },
            'qlab_prores_422_show': {
                'name': 'QLab ProRes 422 Show Pattern',
                'description': 'Realistic show pattern: 1x4K + 3xHD ProRes 422 with crossfades',
                'duration': 9900,  # 2.75 hours = 9900 seconds
                'fio_template': self._get_prores_422_show_config()
            },
            'qlab_prores_hq_show': {
                'name': 'QLab ProRes HQ Show Pattern',
                'description': 'Realistic show pattern: 1x4K + 3xHD ProRes HQ with crossfades',
                'duration': 9900,  # 2.75 hours = 9900 seconds
                'fio_template': self._get_prores_hq_show_config()
            },
            'max_sustained': {
                'name': 'Maximum Sustained Performance',
                'description': 'Continuous maximum load for 1.5 hours (thermal testing)',
                'duration': 5400,  # 1.5 hours = 5400 seconds
                'fio_template': self._get_max_sustained_config()
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
        if test_mode == 'quick_max_speed':
            analysis.update(self._analyze_quick_max_speed(summary))
        elif test_mode == 'qlab_prores_422_show':
            analysis.update(self._analyze_prores_422_show(summary))
        elif test_mode == 'qlab_prores_hq_show':
            analysis.update(self._analyze_prores_hq_show(summary))
        elif test_mode == 'max_sustained':
            analysis.update(self._analyze_max_sustained(summary))
        
        return analysis
    
    def _generate_fio_config(self, template: str, disk_path: str, test_size_gb: int) -> str:
        """Generate FIO config from template with substitutions - filesystem-based only."""
        config = template
        
        # Always use filesystem-based test files for realistic QLab performance
        # QLab reads files from mounted volumes, not raw devices
        if disk_path.startswith('/Volumes/'):
            # External/mounted volume
            test_file = f'{disk_path}/qlab_test_file_{test_size_gb}G'
        elif disk_path == '/' or disk_path == '/System/Volumes/Data':
            # System volume - use /tmp for safety
            test_file = f'/tmp/qlab_test_file_{test_size_gb}G'
        elif disk_path.startswith('/dev/'):
            # Legacy raw device path - convert to filesystem path
            # This shouldn't happen anymore with updated disk detection
            test_file = f'/tmp/qlab_test_file_{test_size_gb}G'
        else:
            # Other mounted filesystem
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
    
    def _get_quick_max_speed_config(self) -> str:
        """Get FIO config for 3-minute maximum read speed test - single continuous job."""
        return """
[global]
ioengine=sync
direct=0
ramp_time=10
runtime=180
time_based=1
group_reporting=1
thread=1
disable_lat=1
disable_clat=1
disable_slat=1
unified_rw_reporting=1

[quick_max_read_speed]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=1M
rw=read
numjobs=4
iodepth=1
"""
    
    def _get_prores_422_show_config(self) -> str:
        """Get FIO config for realistic ProRes 422 show pattern - 2.75 hours with 3 phases, macOS sync engine."""
        return """
[global]
ioengine=sync
direct=0
time_based=1
group_reporting=1
thread=1
disable_lat=1
disable_clat=1
disable_slat=1
unified_rw_reporting=1

# Complete 2.75h Show Simulation (9900 seconds total)
[qlab_prores_422_show_complete]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=1M
rw=randrw
rwmixread=95
numjobs=1
iodepth=1
runtime=9900
ramp_time=60
rate=600M
"""
    
    def _get_prores_hq_show_config(self) -> str:
        """Get FIO config for realistic ProRes HQ show pattern - 2.75 hours with 3 phases."""
        return """
[global]
ioengine=posixaio
direct=0
time_based=1
group_reporting=0
thread=1
norandommap=1
randrepeat=0
log_avg_msec=1000
write_bw_log=show_hq_bw
write_lat_log=show_hq_lat
lat_percentiles=1

# Phase 1: Show Preparation (30 min = 1800s)
# Medien-Preload, Soundcheck-Level - HQ requires more bandwidth
[show_prep_hq]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=2M
rw=read
numjobs=3
iodepth=24
runtime=1800
ramp_time=30
rate=800M

# Phase 2: Normal Show Load (90 min = 5400s)  
# 1x 4K 50p + 3x HD 50p ProRes HQ with crossfades every 3min
[normal_show_hq]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=2M
rw=randrw
rwmixread=98
numjobs=6
iodepth=32
runtime=5400
rate=1400M
rate_process=poisson
thinktime=180000000
startdelay=1800

# Random access for masks and graphics (parallel to show) - HQ needs more
[graphics_access_hq]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=128k
rw=randread
numjobs=3
iodepth=12
runtime=5400
rate=100M
startdelay=1800

# Phase 3: Show Finale (30 min = 1800s)
# Intensive crossfades, maximum load - HQ peak performance
[show_finale_hq]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=4M
rw=read
numjobs=12
iodepth=48
runtime=1800
rate=2800M
rate_process=poisson
startdelay=7200
"""
    
    def _get_max_sustained_config(self) -> str:
        """Get FIO config for 1.5-hour maximum sustained performance test (thermal testing)."""
        return """
[global]
ioengine=posixaio
direct=0
ramp_time=60
runtime=5400
time_based=1
group_reporting=0
thread=1
log_avg_msec=1000
write_bw_log=max_sustained_bw
write_lat_log=max_sustained_lat
lat_percentiles=1

# Continuous maximum sequential read load
[max_sustained_seq_read]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=4M
rw=read
numjobs=6
iodepth=64

# Continuous maximum sequential write load
[max_sustained_seq_write]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=4M
rw=write
numjobs=3
iodepth=32

# Continuous maximum random read load
[max_sustained_rand_read]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=4k
rw=randread
numjobs=12
iodepth=128

# Mixed workload for thermal stress
[max_sustained_mixed]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=1M
rw=randrw
rwmixread=75
numjobs=8
iodepth=64

# Burst pattern to stress thermal limits
[thermal_stress_burst]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=8M
rw=read
numjobs=4
iodepth=32
thinktime=30000000
"""
    
    def _analyze_quick_max_speed(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze quick max speed test results (read-only test)."""
        read_bw = summary.get('total_read_bw', 0) / 1024  # Convert to MB/s
        read_iops = summary.get('total_read_iops', 0)
        avg_latency = summary.get('avg_read_latency', 0)
        
        analysis = {}
        
        # Maximum read performance assessment for QLab video playback
        if read_bw > 1000:
            analysis['overall_performance'] = 'excellent'
            analysis['video_playback_capability'] = 'multiple_4k_streams'
        elif read_bw > 500:
            analysis['overall_performance'] = 'good'
            analysis['video_playback_capability'] = 'single_4k_stream'
        elif read_bw > 200:
            analysis['overall_performance'] = 'fair'
            analysis['video_playback_capability'] = 'hd_streams_only'
        else:
            analysis['overall_performance'] = 'poor'
            analysis['video_playback_capability'] = 'limited'
        
        analysis['audio_cue_performance'] = 'excellent' if read_iops > 10000 else 'good'
        analysis['rapid_triggering_capability'] = 'excellent' if avg_latency < 2 else 'good'
        
        analysis['performance_scores'] = {
            'max_read_mb_s': read_bw,
            'max_read_iops': read_iops,
            'min_latency_ms': avg_latency
        }
        
        return analysis
    
    def _analyze_prores_422_show(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze ProRes 422 show pattern results with thermal analysis."""
        read_bw = summary.get('total_read_bw', 0) / 1024  # Convert to MB/s
        read_iops = summary.get('total_read_iops', 0)
        avg_latency = summary.get('avg_read_latency', 0)
        
        analysis = {}
        
        # Show-specific analysis for ProRes 422 (1x4K + 3xHD = ~700MB/s peak)
        if read_bw > 800:
            analysis['overall_performance'] = 'excellent'
            analysis['video_playback_capability'] = 'show_ready_with_headroom'
            analysis['show_suitability'] = 'professional_ready'
        elif read_bw > 600:
            analysis['overall_performance'] = 'good'
            analysis['video_playback_capability'] = 'show_ready_minimal_headroom'
            analysis['show_suitability'] = 'show_ready'
        elif read_bw > 400:
            analysis['overall_performance'] = 'fair'
            analysis['video_playback_capability'] = 'reduced_streams_only'
            analysis['show_suitability'] = 'limited_show_use'
        else:
            analysis['overall_performance'] = 'poor'
            analysis['video_playback_capability'] = 'unreliable_for_shows'
            analysis['show_suitability'] = 'not_recommended'
        
        # Thermal performance assessment (2.75h test)
        analysis['thermal_performance'] = 'stable' if read_bw > 500 else 'throttling_detected'
        analysis['audio_cue_performance'] = 'excellent' if read_iops > 3000 else 'good'
        analysis['rapid_triggering_capability'] = 'excellent' if avg_latency < 5 else 'good'
        
        analysis['performance_scores'] = {
            'sustained_show_mb_s': read_bw,
            'prores_422_show_capability': 'yes' if read_bw > 600 else 'no',
            'crossfade_headroom': 'yes' if read_bw > 800 else 'limited',
            'thermal_stability': 'stable' if read_bw > 500 else 'degraded'
        }
        
        return analysis
    
    def _analyze_prores_hq_show(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze ProRes HQ show pattern results with thermal analysis."""
        read_bw = summary.get('total_read_bw', 0) / 1024  # Convert to MB/s
        read_iops = summary.get('total_read_iops', 0)
        avg_latency = summary.get('avg_read_latency', 0)
        
        analysis = {}
        
        # Show-specific analysis for ProRes HQ (1x4K + 3xHD = ~1400MB/s peak)
        if read_bw > 1600:
            analysis['overall_performance'] = 'excellent'
            analysis['video_playback_capability'] = 'hq_show_ready_with_headroom'
            analysis['show_suitability'] = 'professional_hq_ready'
        elif read_bw > 1200:
            analysis['overall_performance'] = 'good'
            analysis['video_playback_capability'] = 'hq_show_ready_minimal_headroom'
            analysis['show_suitability'] = 'hq_show_ready'
        elif read_bw > 800:
            analysis['overall_performance'] = 'fair'
            analysis['video_playback_capability'] = 'reduced_hq_streams_only'
            analysis['show_suitability'] = 'limited_hq_show_use'
        else:
            analysis['overall_performance'] = 'poor'
            analysis['video_playback_capability'] = 'unreliable_for_hq_shows'
            analysis['show_suitability'] = 'hq_not_recommended'
        
        # Thermal performance assessment (2.75h test)
        analysis['thermal_performance'] = 'stable' if read_bw > 1000 else 'throttling_detected'
        analysis['audio_cue_performance'] = 'excellent' if read_iops > 5000 else 'good'
        analysis['rapid_triggering_capability'] = 'excellent' if avg_latency < 3 else 'good'
        
        analysis['performance_scores'] = {
            'sustained_hq_show_mb_s': read_bw,
            'prores_hq_show_capability': 'yes' if read_bw > 1200 else 'no',
            'hq_crossfade_headroom': 'yes' if read_bw > 1600 else 'limited',
            'thermal_stability': 'stable' if read_bw > 1000 else 'degraded'
        }
        
        return analysis
    
    def _analyze_max_sustained(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze maximum sustained performance test results (1.5h thermal test)."""
        read_bw = summary.get('total_read_bw', 0) / 1024  # Convert to MB/s
        write_bw = summary.get('total_write_bw', 0) / 1024  # Convert to MB/s
        read_iops = summary.get('total_read_iops', 0)
        avg_latency = summary.get('avg_read_latency', 0)
        
        analysis = {}
        
        # Thermal throttling assessment over 1.5 hours
        if read_bw > 800 and write_bw > 400:
            analysis['overall_performance'] = 'excellent'
            analysis['thermal_performance'] = 'no_throttling_detected'
            analysis['sustained_capability'] = 'professional_grade'
        elif read_bw > 500 and write_bw > 250:
            analysis['overall_performance'] = 'good'
            analysis['thermal_performance'] = 'minimal_throttling'
            analysis['sustained_capability'] = 'show_suitable'
        elif read_bw > 200 and write_bw > 100:
            analysis['overall_performance'] = 'fair'
            analysis['thermal_performance'] = 'moderate_throttling'
            analysis['sustained_capability'] = 'limited_use'
        else:
            analysis['overall_performance'] = 'poor'
            analysis['thermal_performance'] = 'severe_throttling'
            analysis['sustained_capability'] = 'not_recommended'
        
        # Long-term reliability assessment
        analysis['video_playback_capability'] = 'sustained_4k' if read_bw > 600 else 'hd_only'
        analysis['audio_cue_performance'] = 'excellent' if read_iops > 8000 else 'good'
        analysis['rapid_triggering_capability'] = 'excellent' if avg_latency < 5 else 'degraded'
        
        analysis['performance_scores'] = {
            'sustained_read_mb_s': read_bw,
            'sustained_write_mb_s': write_bw,
            'sustained_read_iops': read_iops,
            'thermal_stability_score': 'stable' if read_bw > 400 else 'unstable',
            'long_term_reliability': 'high' if read_bw > 600 else 'medium'
        }
        
        return analysis
