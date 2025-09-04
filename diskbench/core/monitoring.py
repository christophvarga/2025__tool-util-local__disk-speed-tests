"""
Structured logging and performance monitoring for diskbench.

Provides JSON-formatted logging, performance metrics collection,
and operation timing with contextual information.
"""
import logging
import json
import time
import psutil
import os
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from logging.handlers import RotatingFileHandler


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record):
        """Format log record as JSON with contextual information."""
        log_data = {
            'log_ts': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        if hasattr(record, 'extra_fields'):
            extra = dict(record.extra_fields)
            # Avoid timestamp collisions by mapping metric timestamps to event_ts
            if 'timestamp' in extra and 'event_ts' not in extra:
                extra['event_ts'] = extra.pop('timestamp')
            log_data.update(extra)
        
        # Add context from specific fields
        context_fields = ['test_id', 'operation', 'duration', 'status', 'disk_path', 'size_gb']
        for field in context_fields:
            if hasattr(record, field):
                log_data[field] = getattr(record, field)
        
        return json.dumps(log_data, default=str)


class PerformanceMonitor:
    """Monitor system and application performance with metrics collection."""
    
    def __init__(self, log_dir: Optional[str] = None):
        """
        Initialize performance monitor.
        
        Args:
            log_dir: Directory for log files. If None, uses logs/ in current directory.
        """
        self.log_dir = Path(log_dir) if log_dir else Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        self.metrics = {}
        self.start_time = time.time()
        
        # Setup structured logging
        self.setup_logging()
        self.logger = logging.getLogger('diskbench.monitoring')
        
        # Initialize system baseline
        self._system_baseline = self.get_system_metrics()
    
    def setup_logging(self):
        """Setup structured JSON logging with rotation."""
        # Create JSON formatter
        json_formatter = JSONFormatter()
        
        # Setup rotating file handler for structured logs
        json_log_file = self.log_dir / "diskbench.jsonl"
        json_handler = RotatingFileHandler(
            json_log_file,
            maxBytes=50*1024*1024,  # 50MB per file
            backupCount=5
        )
        json_handler.setFormatter(json_formatter)
        json_handler.setLevel(logging.INFO)
        
        # Setup human-readable console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)
        
        # Configure root logger
        root_logger = logging.getLogger('diskbench')
        root_logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        root_logger.addHandler(json_handler)
        root_logger.addHandler(console_handler)
        
        # Prevent propagation to avoid duplicate logs
        root_logger.propagate = False
    
    def log_metric(self, name: str, value: float, tags: Optional[Dict[str, Any]] = None,
                   unit: Optional[str] = None):
        """
        Log a performance metric with tags and context.
        
        Args:
            name: Metric name (e.g., 'fio_execution_duration')
            value: Metric value
            tags: Optional tags for categorization
            unit: Optional unit (e.g., 'seconds', 'bytes', 'iops')
        """
        metric_data = {
            'metric': name,
            'value': value,
            'event_ts': time.time(),
            'tags': tags or {},
            'unit': unit
        }
        
        # Log to structured logger
        logger = logging.getLogger('diskbench.metrics')
        logger.info(
            f"Metric: {name}",
            extra={
                'extra_fields': metric_data,
                'operation': 'metric_collection'
            }
        )
        
        # Store for aggregation
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(metric_data)
        
        # Limit stored metrics to prevent memory issues
        if len(self.metrics[name]) > 1000:
            self.metrics[name] = self.metrics[name][-500:]  # Keep last 500
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive system performance metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk I/O metrics
            disk_io = psutil.disk_io_counters()
            
            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            process_cpu = process.cpu_percent()
            
            # Network metrics (basic)
            network_io = psutil.net_io_counters()
            
            metrics = {
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'frequency_mhz': cpu_freq.current if cpu_freq else None
                },
                'memory': {
                    'total_gb': memory.total / (1024**3),
                    'available_gb': memory.available / (1024**3),
                    'percent_used': memory.percent,
                    'swap_total_gb': swap.total / (1024**3),
                    'swap_used_gb': swap.used / (1024**3)
                },
                'disk_io': {
                    'read_bytes': disk_io.read_bytes if disk_io else 0,
                    'write_bytes': disk_io.write_bytes if disk_io else 0,
                    'read_count': disk_io.read_count if disk_io else 0,
                    'write_count': disk_io.write_count if disk_io else 0
                } if disk_io else {},
                'process': {
                    'memory_mb': process_memory.rss / (1024**2),
                    'cpu_percent': process_cpu,
                    'pid': process.pid,
                    'threads': process.num_threads()
                },
                'network': {
                    'bytes_sent': network_io.bytes_sent if network_io else 0,
                    'bytes_recv': network_io.bytes_recv if network_io else 0
                } if network_io else {},
                'uptime_seconds': time.time() - self.start_time,
                'timestamp': time.time()
            }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            return {
                'error': str(e),
                'timestamp': time.time(),
                'uptime_seconds': time.time() - self.start_time
            }
    
    @contextmanager
    def measure_operation(self, operation_name: str, tags: Optional[Dict[str, Any]] = None):
        """
        Context manager to measure operation duration with detailed logging.
        
        Args:
            operation_name: Name of the operation being measured
            tags: Optional tags for categorization
        """
        start_time = time.time()
        start_metrics = self.get_system_metrics()
        
        logger = logging.getLogger(f'diskbench.operations')
        logger.info(
            f"Starting operation: {operation_name}",
            extra={
                'operation': operation_name,
                'status': 'start',
                'extra_fields': {
                    'tags': tags or {},
                    'system_metrics': start_metrics
                }
            }
        )
        
        exception_occurred = False
        try:
            yield
            
        except Exception as e:
            exception_occurred = True
            end_time = time.time()
            duration = end_time - start_time
            
            logger.error(
                f"Operation failed: {operation_name}",
                extra={
                    'operation': operation_name,
                    'status': 'failure',
                    'duration': duration,
                    'extra_fields': {
                        'tags': tags or {},
                        'error': str(e),
                        'exception_type': type(e).__name__
                    }
                },
                exc_info=True
            )
            
            # Log failure metric
            self.log_metric(
                f'{operation_name}_duration_seconds',
                duration,
                tags={**(tags or {}), 'status': 'failure'},
                unit='seconds'
            )
            
            raise
        
        finally:
            if not exception_occurred:
                end_time = time.time()
                duration = end_time - start_time
                end_metrics = self.get_system_metrics()
                
                logger.info(
                    f"Operation completed: {operation_name}",
                    extra={
                        'operation': operation_name,
                        'status': 'success',
                        'duration': duration,
                        'extra_fields': {
                            'tags': tags or {},
                            'system_metrics_delta': self._calculate_metrics_delta(start_metrics, end_metrics)
                        }
                    }
                )
                
                # Log success metric
                self.log_metric(
                    f'{operation_name}_duration_seconds',
                    duration,
                    tags={**(tags or {}), 'status': 'success'},
                    unit='seconds'
                )
    
    def _calculate_metrics_delta(self, start_metrics: Dict[str, Any], 
                                end_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate difference between start and end metrics."""
        try:
            delta = {}
            
            # CPU delta
            if 'cpu' in start_metrics and 'cpu' in end_metrics:
                delta['cpu_percent_change'] = (
                    end_metrics['cpu']['percent'] - start_metrics['cpu']['percent']
                )
            
            # Memory delta
            if 'memory' in start_metrics and 'memory' in end_metrics:
                delta['memory_used_change_mb'] = (
                    (start_metrics['memory']['total_gb'] - end_metrics['memory']['available_gb']) -
                    (start_metrics['memory']['total_gb'] - start_metrics['memory']['available_gb'])
                ) * 1024
            
            # Disk I/O delta
            if ('disk_io' in start_metrics and 'disk_io' in end_metrics and
                start_metrics['disk_io'] and end_metrics['disk_io']):
                delta['disk_read_bytes'] = (
                    end_metrics['disk_io']['read_bytes'] - start_metrics['disk_io']['read_bytes']
                )
                delta['disk_write_bytes'] = (
                    end_metrics['disk_io']['write_bytes'] - start_metrics['disk_io']['write_bytes']
                )
            
            # Process memory delta
            if 'process' in start_metrics and 'process' in end_metrics:
                delta['process_memory_change_mb'] = (
                    end_metrics['process']['memory_mb'] - start_metrics['process']['memory_mb']
                )
            
            return delta
            
        except Exception as e:
            return {'error': f'Failed to calculate metrics delta: {e}'}
    
    def get_metric_summary(self, metric_name: str) -> Dict[str, Any]:
        """Get statistical summary of a collected metric."""
        if metric_name not in self.metrics:
            return {'error': f'Metric {metric_name} not found'}
        
        values = [m['value'] for m in self.metrics[metric_name]]
        
        if not values:
            return {'error': 'No values for metric'}
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'latest': values[-1] if values else None,
            'unit': self.metrics[metric_name][-1].get('unit') if self.metrics[metric_name] else None
        }
    
    def export_metrics(self, output_file: Optional[str] = None) -> str:
        """Export collected metrics to JSON file."""
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'system_baseline': self._system_baseline,
            'current_system_metrics': self.get_system_metrics(),
            'collected_metrics': self.metrics,
            'metric_summaries': {
                name: self.get_metric_summary(name) 
                for name in self.metrics.keys()
            }
        }
        
        if output_file is None:
            output_file = str(self.log_dir / f"metrics_export_{int(time.time())}.json")
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        return output_file
    
    def clear_metrics(self):
        """Clear collected metrics to free memory."""
        cleared_count = sum(len(metrics) for metrics in self.metrics.values())
        self.metrics.clear()
        self.logger.info(f"Cleared {cleared_count} collected metrics")
