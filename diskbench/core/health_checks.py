"""
System health checks for diskbench monitoring.

Provides comprehensive health monitoring including disk health,
system resources, dependencies, and operational status checks.
"""
import os
import subprocess
import shutil
import time
import psutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from .monitoring import PerformanceMonitor


class HealthStatus(Enum):
    """Health check status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check operation."""
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    timestamp: float
    duration_ms: float


class SystemHealthChecker:
    """Comprehensive system health monitoring for diskbench."""
    
    def __init__(self, monitor: Optional[PerformanceMonitor] = None):
        """
        Initialize health checker.
        
        Args:
            monitor: Optional performance monitor for metrics logging
        """
        self.monitor = monitor
        self.last_check_time = 0
        self.check_interval = 60  # Default check every 60 seconds
        
        # Thresholds for health checks
        self.thresholds = {
            'disk_space_warning_percent': 85,
            'disk_space_critical_percent': 95,
            'memory_warning_percent': 85,
            'memory_critical_percent': 95,
            'cpu_warning_percent': 90,
            'cpu_critical_percent': 98,
            'disk_io_latency_warning_ms': 100,
            'disk_io_latency_critical_ms': 500,
            'temperature_warning_celsius': 80,
            'temperature_critical_celsius': 90
        }
    
    def run_all_checks(self) -> List[HealthCheckResult]:
        """
        Run all available health checks.
        
        Returns:
            List of health check results
        """
        checks = [
            self.check_disk_health,
            self.check_memory_usage,
            self.check_cpu_usage,
            self.check_disk_space,
            self.check_fio_dependency,
            self.check_system_temperatures,
            self.check_disk_io_performance,
            self.check_network_connectivity,
            self.check_process_health
        ]
        
        results = []
        start_time = time.time()
        
        for check_func in checks:
            try:
                result = check_func()
                results.append(result)
                
                # Log metrics if monitor available
                if self.monitor:
                    self.monitor.log_metric(
                        f'health_check_{result.name}_duration_ms',
                        result.duration_ms,
                        tags={
                            'status': result.status.value,
                            'check_name': result.name
                        },
                        unit='milliseconds'
                    )
                    
            except Exception as e:
                error_result = HealthCheckResult(
                    name=check_func.__name__.replace('check_', ''),
                    status=HealthStatus.CRITICAL,
                    message=f"Health check failed: {e}",
                    details={'exception': str(e), 'exception_type': type(e).__name__},
                    timestamp=time.time(),
                    duration_ms=0
                )
                results.append(error_result)
        
        total_duration = (time.time() - start_time) * 1000
        
        # Log overall health check metrics
        if self.monitor:
            healthy_count = sum(1 for r in results if r.status == HealthStatus.HEALTHY)
            warning_count = sum(1 for r in results if r.status == HealthStatus.WARNING)
            critical_count = sum(1 for r in results if r.status == HealthStatus.CRITICAL)
            
            self.monitor.log_metric('health_checks_total_duration_ms', total_duration, unit='milliseconds')
            self.monitor.log_metric('health_checks_healthy_count', healthy_count, unit='count')
            self.monitor.log_metric('health_checks_warning_count', warning_count, unit='count')
            self.monitor.log_metric('health_checks_critical_count', critical_count, unit='count')
        
        self.last_check_time = time.time()
        return results
    
    def check_disk_health(self) -> HealthCheckResult:
        """Check disk health using SMART data and basic disk information."""
        start_time = time.time()
        
        try:
            # Get disk usage information
            disks_info = []
            for disk_partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(disk_partition.mountpoint)
                    disks_info.append({
                        'device': disk_partition.device,
                        'mountpoint': disk_partition.mountpoint,
                        'fstype': disk_partition.fstype,
                        'total_gb': usage.total / (1024**3),
                        'free_gb': usage.free / (1024**3),
                        'used_percent': (usage.used / usage.total) * 100
                    })
                except (PermissionError, OSError):
                    continue
            
            # Try to get SMART data (macOS specific)
            smart_data = self._get_smart_data()
            
            # Determine overall status
            critical_issues = []
            warnings = []
            
            # Check for disk space issues
            for disk in disks_info:
                if disk['used_percent'] > self.thresholds['disk_space_critical_percent']:
                    critical_issues.append(f"Disk {disk['device']} critically low space: {disk['used_percent']:.1f}% used")
                elif disk['used_percent'] > self.thresholds['disk_space_warning_percent']:
                    warnings.append(f"Disk {disk['device']} low space warning: {disk['used_percent']:.1f}% used")
            
            # Check SMART data if available
            if smart_data and 'errors' in smart_data:
                for error in smart_data['errors']:
                    critical_issues.append(f"SMART error: {error}")
            
            # Determine status
            if critical_issues:
                status = HealthStatus.CRITICAL
                message = f"Critical disk issues detected: {'; '.join(critical_issues[:3])}"
            elif warnings:
                status = HealthStatus.WARNING
                message = f"Disk warnings: {'; '.join(warnings[:3])}"
            else:
                status = HealthStatus.HEALTHY
                message = f"All {len(disks_info)} disk(s) healthy"
            
            return HealthCheckResult(
                name="disk_health",
                status=status,
                message=message,
                details={
                    'disks': disks_info,
                    'smart_data': smart_data,
                    'critical_issues': critical_issues,
                    'warnings': warnings
                },
                timestamp=time.time(),
                duration_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="disk_health",
                status=HealthStatus.CRITICAL,
                message=f"Failed to check disk health: {e}",
                details={'error': str(e)},
                timestamp=time.time(),
                duration_ms=(time.time() - start_time) * 1000
            )
    
    def _get_smart_data(self) -> Optional[Dict[str, Any]]:
        """Attempt to get SMART data from disks (macOS/Unix specific)."""
        try:
            # Try using smartctl if available
            if shutil.which('smartctl'):
                # Get list of devices
                result = subprocess.run(
                    ['smartctl', '--scan'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    devices = []
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            device = line.split()[0]
                            devices.append(device)
                    
                    smart_info = {'devices': devices, 'health_status': {}, 'errors': []}
                    
                    # Check health for each device
                    for device in devices[:3]:  # Limit to first 3 devices
                        try:
                            health_result = subprocess.run(
                                ['smartctl', '-H', device],
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                            
                            if 'PASSED' in health_result.stdout:
                                smart_info['health_status'][device] = 'PASSED'
                            elif 'FAILED' in health_result.stdout:
                                smart_info['health_status'][device] = 'FAILED'
                                smart_info['errors'].append(f"SMART health check failed for {device}")
                            
                        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                            continue
                    
                    return smart_info
            
            return None
            
        except Exception:
            return None
    
    def check_memory_usage(self) -> HealthCheckResult:
        """Check system memory usage and availability."""
        start_time = time.time()
        
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            memory_percent = memory.percent
            swap_percent = swap.percent if swap.total > 0 else 0
            
            # Determine status
            if (memory_percent > self.thresholds['memory_critical_percent'] or 
                swap_percent > 90):
                status = HealthStatus.CRITICAL
                message = f"Critical memory usage: RAM {memory_percent:.1f}%, Swap {swap_percent:.1f}%"
            elif memory_percent > self.thresholds['memory_warning_percent']:
                status = HealthStatus.WARNING
                message = f"High memory usage warning: RAM {memory_percent:.1f}%, Swap {swap_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory usage healthy: RAM {memory_percent:.1f}%, Swap {swap_percent:.1f}%"
            
            return HealthCheckResult(
                name="memory_usage",
                status=status,
                message=message,
                details={
                    'memory': {
                        'total_gb': memory.total / (1024**3),
                        'available_gb': memory.available / (1024**3),
                        'used_percent': memory_percent,
                        'free_gb': memory.free / (1024**3)
                    },
                    'swap': {
                        'total_gb': swap.total / (1024**3),
                        'used_gb': swap.used / (1024**3),
                        'used_percent': swap_percent
                    }
                },
                timestamp=time.time(),
                duration_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="memory_usage",
                status=HealthStatus.CRITICAL,
                message=f"Failed to check memory usage: {e}",
                details={'error': str(e)},
                timestamp=time.time(),
                duration_ms=(time.time() - start_time) * 1000
            )
    
    def check_cpu_usage(self) -> HealthCheckResult:
        """Check CPU usage and load average."""
        start_time = time.time()
        
        try:
            # Get CPU usage over a short interval
            cpu_percent = psutil.cpu_percent(interval=0.5)
            cpu_count = psutil.cpu_count()
            
            # Get load average (Unix systems)
            try:
                load_avg = os.getloadavg()
                load_avg_1min = load_avg[0]
                load_avg_normalized = (load_avg_1min / cpu_count) * 100
            except (OSError, AttributeError):
                load_avg = None
                load_avg_normalized = None
            
            # CPU frequency info
            try:
                cpu_freq = psutil.cpu_freq()
                cpu_freq_current = cpu_freq.current if cpu_freq else None
            except (OSError, AttributeError):
                cpu_freq_current = None
            
            # Determine status based on CPU usage
            if cpu_percent > self.thresholds['cpu_critical_percent']:
                status = HealthStatus.CRITICAL
                message = f"Critical CPU usage: {cpu_percent:.1f}%"
            elif cpu_percent > self.thresholds['cpu_warning_percent']:
                status = HealthStatus.WARNING
                message = f"High CPU usage warning: {cpu_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"CPU usage healthy: {cpu_percent:.1f}%"
            
            # Add load average to message if available
            if load_avg_normalized is not None:
                message += f", Load: {load_avg_normalized:.1f}%"
            
            return HealthCheckResult(
                name="cpu_usage",
                status=status,
                message=message,
                details={
                    'cpu_percent': cpu_percent,
                    'cpu_count': cpu_count,
                    'load_average': load_avg,
                    'load_average_normalized_percent': load_avg_normalized,
                    'cpu_frequency_mhz': cpu_freq_current
                },
                timestamp=time.time(),
                duration_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="cpu_usage",
                status=HealthStatus.CRITICAL,
                message=f"Failed to check CPU usage: {e}",
                details={'error': str(e)},
                timestamp=time.time(),
                duration_ms=(time.time() - start_time) * 1000
            )
    
    def check_disk_space(self) -> HealthCheckResult:
        """Check available disk space for all mounted filesystems."""
        start_time = time.time()
        
        try:
            partitions = psutil.disk_partitions()
            disk_info = []
            critical_disks = []
            warning_disks = []
            
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    used_percent = (usage.used / usage.total) * 100
                    
                    disk_data = {
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total_gb': usage.total / (1024**3),
                        'used_gb': usage.used / (1024**3),
                        'free_gb': usage.free / (1024**3),
                        'used_percent': used_percent
                    }
                    disk_info.append(disk_data)
                    
                    # Check thresholds
                    if used_percent > self.thresholds['disk_space_critical_percent']:
                        critical_disks.append(f"{partition.mountpoint}: {used_percent:.1f}% used")
                    elif used_percent > self.thresholds['disk_space_warning_percent']:
                        warning_disks.append(f"{partition.mountpoint}: {used_percent:.1f}% used")
                        
                except (PermissionError, OSError):
                    continue
            
            # Determine overall status
            if critical_disks:
                status = HealthStatus.CRITICAL
                message = f"Critical disk space on {len(critical_disks)} disk(s): {critical_disks[0]}"
            elif warning_disks:
                status = HealthStatus.WARNING
                message = f"Low disk space warning on {len(warning_disks)} disk(s): {warning_disks[0]}"
            else:
                status = HealthStatus.HEALTHY
                message = f"Disk space healthy on all {len(disk_info)} disk(s)"
            
            return HealthCheckResult(
                name="disk_space",
                status=status,
                message=message,
                details={
                    'disks': disk_info,
                    'critical_disks': critical_disks,
                    'warning_disks': warning_disks
                },
                timestamp=time.time(),
                duration_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="disk_space",
                status=HealthStatus.CRITICAL,
                message=f"Failed to check disk space: {e}",
                details={'error': str(e)},
                timestamp=time.time(),
                duration_ms=(time.time() - start_time) * 1000
            )
    
    def check_fio_dependency(self) -> HealthCheckResult:
        """Check FIO availability and basic functionality."""
        start_time = time.time()
        
        try:
            # Check if FIO is available
            fio_path = shutil.which('fio')
            
            if not fio_path:
                return HealthCheckResult(
                    name="fio_dependency",
                    status=HealthStatus.CRITICAL,
                    message="FIO not found in system PATH",
                    details={'fio_path': None, 'error': 'FIO executable not found'},
                    timestamp=time.time(),
                    duration_ms=(time.time() - start_time) * 1000
                )
            
            # Try to get FIO version
            try:
                version_result = subprocess.run(
                    [fio_path, '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if version_result.returncode == 0:
                    fio_version = version_result.stdout.strip()
                    
                    # Try a simple FIO test to verify functionality
                    test_result = subprocess.run(
                        [fio_path, '--help'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    if test_result.returncode == 0:
                        status = HealthStatus.HEALTHY
                        message = f"FIO available and functional: {fio_version}"
                    else:
                        status = HealthStatus.WARNING
                        message = f"FIO found but help command failed: {fio_version}"
                    
                    return HealthCheckResult(
                        name="fio_dependency",
                        status=status,
                        message=message,
                        details={
                            'fio_path': fio_path,
                            'fio_version': fio_version,
                            'version_check_success': version_result.returncode == 0,
                            'help_check_success': test_result.returncode == 0
                        },
                        timestamp=time.time(),
                        duration_ms=(time.time() - start_time) * 1000
                    )
                else:
                    return HealthCheckResult(
                        name="fio_dependency",
                        status=HealthStatus.WARNING,
                        message="FIO found but version check failed",
                        details={
                            'fio_path': fio_path,
                            'version_check_error': version_result.stderr
                        },
                        timestamp=time.time(),
                        duration_ms=(time.time() - start_time) * 1000
                    )
                    
            except subprocess.TimeoutExpired:
                return HealthCheckResult(
                    name="fio_dependency",
                    status=HealthStatus.WARNING,
                    message="FIO found but version check timed out",
                    details={'fio_path': fio_path, 'error': 'Version check timeout'},
                    timestamp=time.time(),
                    duration_ms=(time.time() - start_time) * 1000
                )
                
        except Exception as e:
            return HealthCheckResult(
                name="fio_dependency",
                status=HealthStatus.CRITICAL,
                message=f"Failed to check FIO dependency: {e}",
                details={'error': str(e)},
                timestamp=time.time(),
                duration_ms=(time.time() - start_time) * 1000
            )
    
    def check_system_temperatures(self) -> HealthCheckResult:
        """Check system temperatures if available."""
        start_time = time.time()
        
        try:
            # Try to get temperature sensors (may not work on all systems)
            try:
                if hasattr(psutil, 'sensors_temperatures'):
                    temps = psutil.sensors_temperatures()
                    if temps:
                        temp_info = []
                        critical_temps = []
                        warning_temps = []
                        
                        for sensor_name, sensor_list in temps.items():
                            for sensor in sensor_list:
                                temp_data = {
                                    'sensor': f"{sensor_name}_{sensor.label or 'unknown'}",
                                    'temperature_celsius': sensor.current,
                                    'high_threshold': sensor.high,
                                    'critical_threshold': sensor.critical
                                }
                                temp_info.append(temp_data)
                                
                                # Check thresholds
                                if sensor.current > self.thresholds['temperature_critical_celsius']:
                                    critical_temps.append(f"{temp_data['sensor']}: {sensor.current:.1f}°C")
                                elif sensor.current > self.thresholds['temperature_warning_celsius']:
                                    warning_temps.append(f"{temp_data['sensor']}: {sensor.current:.1f}°C")
                        
                        # Determine status
                        if critical_temps:
                            status = HealthStatus.CRITICAL
                            message = f"Critical temperatures detected: {critical_temps[0]}"
                        elif warning_temps:
                            status = HealthStatus.WARNING
                            message = f"High temperature warnings: {warning_temps[0]}"
                        else:
                            status = HealthStatus.HEALTHY
                            message = f"System temperatures healthy ({len(temp_info)} sensors)"
                        
                        return HealthCheckResult(
                            name="system_temperatures",
                            status=status,
                            message=message,
                            details={
                                'temperatures': temp_info,
                                'critical_temps': critical_temps,
                                'warning_temps': warning_temps
                            },
                            timestamp=time.time(),
                            duration_ms=(time.time() - start_time) * 1000
                        )
                    else:
                        return HealthCheckResult(
                            name="system_temperatures",
                            status=HealthStatus.UNKNOWN,
                            message="No temperature sensors found",
                            details={'sensors_available': False},
                            timestamp=time.time(),
                            duration_ms=(time.time() - start_time) * 1000
                        )
                else:
                    return HealthCheckResult(
                        name="system_temperatures",
                        status=HealthStatus.UNKNOWN,
                        message="Temperature monitoring not supported on this system",
                        details={'psutil_sensors_support': False},
                        timestamp=time.time(),
                        duration_ms=(time.time() - start_time) * 1000
                    )
                    
            except Exception:
                return HealthCheckResult(
                    name="system_temperatures",
                    status=HealthStatus.UNKNOWN,
                    message="Temperature sensors not accessible",
                    details={'sensor_access_error': True},
                    timestamp=time.time(),
                    duration_ms=(time.time() - start_time) * 1000
                )
                
        except Exception as e:
            return HealthCheckResult(
                name="system_temperatures",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check system temperatures: {e}",
                details={'error': str(e)},
                timestamp=time.time(),
                duration_ms=(time.time() - start_time) * 1000
            )
    
    def check_disk_io_performance(self) -> HealthCheckResult:
        """Check basic disk I/O performance and latency."""
        start_time = time.time()
        
        try:
            # Get initial disk I/O counters
            initial_io = psutil.disk_io_counters()
            if not initial_io:
                return HealthCheckResult(
                    name="disk_io_performance",
                    status=HealthStatus.UNKNOWN,
                    message="Disk I/O counters not available",
                    details={'io_counters_available': False},
                    timestamp=time.time(),
                    duration_ms=(time.time() - start_time) * 1000
                )
            
            # Wait a short time and measure again
            time.sleep(0.5)
            final_io = psutil.disk_io_counters()
            
            # Calculate I/O metrics
            read_bytes_diff = final_io.read_bytes - initial_io.read_bytes
            write_bytes_diff = final_io.write_bytes - initial_io.write_bytes
            read_count_diff = final_io.read_count - initial_io.read_count
            write_count_diff = final_io.write_count - initial_io.write_count
            
            # Calculate approximate latency
            total_io_ops = read_count_diff + write_count_diff
            if total_io_ops > 0:
                # This is a rough approximation
                avg_latency_ms = (0.5 * 1000) / total_io_ops  # Very rough estimate
            else:
                avg_latency_ms = 0
            
            # Check against thresholds (very basic check)
            if avg_latency_ms > self.thresholds['disk_io_latency_critical_ms']:
                status = HealthStatus.CRITICAL
                message = f"Critical disk I/O latency: {avg_latency_ms:.2f}ms avg"
            elif avg_latency_ms > self.thresholds['disk_io_latency_warning_ms']:
                status = HealthStatus.WARNING
                message = f"High disk I/O latency: {avg_latency_ms:.2f}ms avg"
            else:
                status = HealthStatus.HEALTHY
                message = f"Disk I/O performance healthy: {avg_latency_ms:.2f}ms avg latency"
            
            return HealthCheckResult(
                name="disk_io_performance",
                status=status,
                message=message,
                details={
                    'measurement_interval_seconds': 0.5,
                    'read_bytes_per_second': read_bytes_diff * 2,
                    'write_bytes_per_second': write_bytes_diff * 2,
                    'read_ops_per_second': read_count_diff * 2,
                    'write_ops_per_second': write_count_diff * 2,
                    'estimated_avg_latency_ms': avg_latency_ms,
                    'total_io_ops': total_io_ops
                },
                timestamp=time.time(),
                duration_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="disk_io_performance",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check disk I/O performance: {e}",
                details={'error': str(e)},
                timestamp=time.time(),
                duration_ms=(time.time() - start_time) * 1000
            )
    
    def check_network_connectivity(self) -> HealthCheckResult:
        """Check basic network connectivity."""
        start_time = time.time()
        
        try:
            # Basic network interface check
            network_interfaces = psutil.net_if_addrs()
            active_interfaces = []
            
            for interface_name, interface_addresses in network_interfaces.items():
                if interface_name.startswith('lo'):  # Skip loopback
                    continue
                    
                for address in interface_addresses:
                    if address.family == 2:  # IPv4
                        active_interfaces.append({
                            'interface': interface_name,
                            'ip': address.address,
                            'netmask': address.netmask
                        })
            
            # Get network I/O stats
            try:
                net_io = psutil.net_io_counters()
                network_stats = {
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv,
                    'errors_in': net_io.errin,
                    'errors_out': net_io.errout,
                    'dropped_in': net_io.dropin,
                    'dropped_out': net_io.dropout
                } if net_io else {}
            except:
                network_stats = {}
            
            # Determine status
            if not active_interfaces:
                status = HealthStatus.WARNING
                message = "No active network interfaces found"
            elif network_stats.get('errors_in', 0) > 1000 or network_stats.get('errors_out', 0) > 1000:
                status = HealthStatus.WARNING
                message = f"High network error count detected"
            else:
                status = HealthStatus.HEALTHY
                message = f"Network connectivity healthy ({len(active_interfaces)} active interfaces)"
            
            return HealthCheckResult(
                name="network_connectivity",
                status=status,
                message=message,
                details={
                    'active_interfaces': active_interfaces,
                    'network_stats': network_stats
                },
                timestamp=time.time(),
                duration_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="network_connectivity",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check network connectivity: {e}",
                details={'error': str(e)},
                timestamp=time.time(),
                duration_ms=(time.time() - start_time) * 1000
            )
    
    def check_process_health(self) -> HealthCheckResult:
        """Check health of current process and system processes."""
        start_time = time.time()
        
        try:
            # Current process info
            current_process = psutil.Process()
            process_info = {
                'pid': current_process.pid,
                'memory_mb': current_process.memory_info().rss / (1024**2),
                'cpu_percent': current_process.cpu_percent(),
                'num_threads': current_process.num_threads(),
                'status': current_process.status(),
                'create_time': current_process.create_time(),
                'uptime_seconds': time.time() - current_process.create_time()
            }
            
            # System process counts
            system_stats = {
                'total_processes': len(psutil.pids()),
                'running_processes': len([p for p in psutil.process_iter(['status']) 
                                        if p.info['status'] == 'running']),
                'sleeping_processes': len([p for p in psutil.process_iter(['status']) 
                                         if p.info['status'] == 'sleeping'])
            }
            
            # Check for issues
            warnings = []
            if process_info['memory_mb'] > 1000:  # > 1GB
                warnings.append(f"High memory usage: {process_info['memory_mb']:.1f}MB")
            
            if process_info['num_threads'] > 50:
                warnings.append(f"High thread count: {process_info['num_threads']}")
            
            # Determine status
            if warnings:
                status = HealthStatus.WARNING
                message = f"Process health warnings: {'; '.join(warnings)}"
            else:
                status = HealthStatus.HEALTHY
                message = f"Process health good (PID: {process_info['pid']}, Memory: {process_info['memory_mb']:.1f}MB)"
            
            return HealthCheckResult(
                name="process_health",
                status=status,
                message=message,
                details={
                    'current_process': process_info,
                    'system_stats': system_stats,
                    'warnings': warnings
                },
                timestamp=time.time(),
                duration_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="process_health",
                status=HealthStatus.CRITICAL,
                message=f"Failed to check process health: {e}",
                details={'error': str(e)},
                timestamp=time.time(),
                duration_ms=(time.time() - start_time) * 1000
            )
    
    def get_health_summary(self, results: Optional[List[HealthCheckResult]] = None) -> Dict[str, Any]:
        """
        Get summary of health check results.
        
        Args:
            results: Health check results. If None, runs all checks.
            
        Returns:
            Dictionary with health summary
        """
        if results is None:
            results = self.run_all_checks()
        
        summary = {
            'timestamp': time.time(),
            'total_checks': len(results),
            'healthy': sum(1 for r in results if r.status == HealthStatus.HEALTHY),
            'warnings': sum(1 for r in results if r.status == HealthStatus.WARNING),
            'critical': sum(1 for r in results if r.status == HealthStatus.CRITICAL),
            'unknown': sum(1 for r in results if r.status == HealthStatus.UNKNOWN),
            'overall_status': self._determine_overall_status(results),
            'details': [asdict(result) for result in results]
        }
        
        return summary
    
    def _determine_overall_status(self, results: List[HealthCheckResult]) -> str:
        """Determine overall system health status."""
        if any(r.status == HealthStatus.CRITICAL for r in results):
            return "critical"
        elif any(r.status == HealthStatus.WARNING for r in results):
            return "warning"
        elif all(r.status == HealthStatus.HEALTHY for r in results):
            return "healthy"
        else:
            return "unknown"
