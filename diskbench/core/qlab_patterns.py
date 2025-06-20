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
                'name': 'Test 1: Quick Max Read Test',
                'description': 'Maximum sequential read performance - 3 minutes',
                'duration': 180,  # 3 minutes
                'fio_template': self._get_quick_max_speed_config()
            },
            'qlab_prores_422_show': {
                'name': 'Test 2: ProRes 422 Production Test',
                'description': 'Scenario: 1x 4K ProRes 422 + 3x HD ProRes 422 @ 50fps - 2.5 hours',
                'duration': 9000,  # 2.5 hours = 9000 seconds
                'fio_template': self._get_prores_422_show_config()
            },
            'qlab_prores_hq_show': {
                'name': 'Test 3: ProRes HQ Production Test',
                'description': 'Scenario: 1x 4K ProRes HQ + 3x HD ProRes HQ @ 50fps - 2.5 hours',
                'duration': 9000,  # 2.5 hours = 9000 seconds
                'fio_template': self._get_prores_hq_show_config()
            },
            'max_sustained': {
                'name': 'Test 4: Max Sustained Read',
                'description': 'Find reliable minimum speed under maximum stress - 1 hour',
                'duration': 3600,  # 1 hour = 3600 seconds
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
        """Get FIO config for 3-minute maximum read speed test - fixed for macOS compatibility."""
        return """
[global]
ioengine=posixaio
direct=0
runtime=180
time_based=1
thread=1
log_avg_msec=1000
write_bw_log=quick_max_bw
write_lat_log=quick_max_lat
write_iops_log=quick_max_iops

[quick_max_read]
filename=${TEST_FILE}
size=10G
bs=4M
rw=read
numjobs=1
iodepth=64
"""
    
    def _get_prores_422_show_config(self) -> str:
        """Get FIO config for realistic ProRes 422 show pattern - 2.5 hours with 3 phases."""
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
write_bw_log=p422_show_bw
write_lat_log=p422_show_lat
lat_percentiles=1

# Phase 1: ProRes 422 Warmup + Asset Cache (30 min = 1800s)
[p422_warmup]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=1M,64K,4K
rw=randrw
rwmixread=93
numjobs=4
runtime=1800
rate=400M,50M
iodepth=24
ramp_time=30

# Phase 2: ProRes 422 Show + Continuous Asset Access (90 min = 5400s)
[p422_show_with_assets]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=1M,256K,16K
rw=randrw
rwmixread=96
numjobs=6
runtime=5400
rate=700M,100M
rate_process=poisson
iodepth=32
thinktime=12000000
thinktime_spin=3000000
startdelay=1800

# Phase 3: ProRes 422 Peak + Heavy Asset Load (30 min = 1800s)
[p422_peak_assets]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=2M,128K,8K
rw=randrw
rwmixread=94
numjobs=8
runtime=1800
rate=2000M,200M
rate_process=poisson
iodepth=48
startdelay=7200

# Cue Response Time Test (5 min = 300s)
[cue_response]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=4K,64K,1M
rw=randread
numjobs=12
runtime=300
iodepth=1
startdelay=9000
"""
    
    def _get_prores_hq_show_config(self) -> str:
        """Get FIO config for realistic ProRes HQ show pattern - 2.5 hours with 3 phases."""
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
write_bw_log=hq_show_bw
write_lat_log=hq_show_lat
lat_percentiles=1

# Phase 1: ProRes HQ Warmup & Asset Loading (30 min = 1800s)
[hq_warmup]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=1M,256K
rw=randrw
rwmixread=95
numjobs=3
runtime=1800
rate=600M
iodepth=16
ramp_time=30

# Phase 2: ProRes HQ Normal Show Operations (90 min = 5400s)
[hq_normal_show]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=2M,512K
rw=randrw
rwmixread=97
numjobs=6
runtime=5400
rate=1400M
rate_process=poisson
iodepth=32
thinktime=8000000
thinktime_spin=2000000
startdelay=1800

# Phase 3: ProRes HQ Peak Performance & Multiple Crossfades (30 min = 1800s)
[hq_peak_crossfades]
filename=${TEST_FILE}
size=${TEST_SIZE}
bs=4M
rw=read
numjobs=10
runtime=1800
rate=4000M
rate_process=poisson
iodepth=64
startdelay=7200
"""
    
    def _get_max_sustained_config(self) -> str:
        """Get FIO config for 1-hour maximum sustained performance test (thermal testing)."""
        return """
[global]
ioengine=posixaio
direct=0
time_based=1
group_reporting=0
thread=1
log_avg_msec=1000
write_bw_log=sustained_bw
write_lat_log=sustained_lat
lat_percentiles=1

# Graduated load tests to find performance ceiling
# Test rates: 500, 750, 1000, 1250, 1500, 1750, 2000, 2250, 2500, 2750, 3000, 3500, 4000, 4500, 5000, 6000 MB/s
# Each rate tested for 4 minutes (240s) for reliable measurement

[sustained_500M]
filename=${TEST_FILE}
size=50G
bs=8M
rw=read
numjobs=4
runtime=240
rate=500M
iodepth=64

[sustained_750M]
filename=${TEST_FILE}
size=50G
bs=8M
rw=read
numjobs=4
runtime=240
rate=750M
iodepth=64
startdelay=240

[sustained_1000M]
filename=${TEST_FILE}
size=50G
bs=8M
rw=read
numjobs=4
runtime=240
rate=1000M
iodepth=64
startdelay=480

[sustained_1250M]
filename=${TEST_FILE}
size=50G
bs=8M
rw=read
numjobs=4
runtime=240
rate=1250M
iodepth=64
startdelay=720

[sustained_1500M]
filename=${TEST_FILE}
size=50G
bs=8M
rw=read
numjobs=4
runtime=240
rate=1500M
iodepth=64
startdelay=960

[sustained_1750M]
filename=${TEST_FILE}
size=50G
bs=8M
rw=read
numjobs=4
runtime=240
rate=1750M
iodepth=64
startdelay=1200

[sustained_2000M]
filename=${TEST_FILE}
size=50G
bs=8M
rw=read
numjobs=4
runtime=240
rate=2000M
iodepth=64
startdelay=1440

# Final validation at reliable speed (15 minutes)
[final_validation]
filename=${TEST_FILE}
size=50G
bs=8M
rw=read
numjobs=4
runtime=900
rate=1500M
iodepth=64
startdelay=1680
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
