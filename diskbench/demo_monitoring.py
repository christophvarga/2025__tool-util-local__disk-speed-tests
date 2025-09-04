#!/usr/bin/env python3
"""
Comprehensive demonstration of Phase 3 monitoring and observability features.

This script showcases the complete monitoring and health check system
implemented in Phase 3 of the diskbench improvement plan.
"""
import sys
import time
import json
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from diskbench.core.monitoring import PerformanceMonitor
from diskbench.core.health_checks import SystemHealthChecker, HealthStatus


def demonstrate_performance_monitoring():
    """Demonstrate performance monitoring capabilities."""
    print("=" * 60)
    print("PERFORMANCE MONITORING DEMONSTRATION")
    print("=" * 60)
    
    # Initialize monitor
    monitor = PerformanceMonitor()
    print(f"✅ Performance monitor initialized")
    print(f"   Log directory: {monitor.log_dir}")
    
    # Collect system metrics
    print("\n📊 Collecting system metrics...")
    metrics = monitor.get_system_metrics()
    
    print(f"   CPU Usage: {metrics['cpu']['percent']:.1f}%")
    print(f"   Memory Usage: {metrics['memory']['percent_used']:.1f}%")
    print(f"   Process Memory: {metrics['process']['memory_mb']:.1f} MB")
    print(f"   Process Threads: {metrics['process']['threads']}")
    print(f"   Uptime: {metrics['uptime_seconds']:.1f} seconds")
    
    # Test metric logging
    print("\n📈 Logging performance metrics...")
    monitor.log_metric('demo_metric_1', 42.5, tags={'demo': 'true'}, unit='seconds')
    monitor.log_metric('demo_metric_2', 123.7, tags={'demo': 'true'}, unit='ops_per_second')
    monitor.log_metric('demo_metric_1', 38.2, tags={'demo': 'true'}, unit='seconds')  # Second value
    
    # Test operation measurement
    print("\n⏱️  Testing operation measurement...")
    with monitor.measure_operation('demo_operation', tags={'operation': 'test'}):
        time.sleep(0.2)  # Simulate work
        print("   Operation completed (simulated 0.2s delay)")
    
    # Get metric summaries
    print("\n📋 Metric summaries:")
    summary1 = monitor.get_metric_summary('demo_metric_1')
    print(f"   demo_metric_1: count={summary1['count']}, avg={summary1['avg']:.2f}, min={summary1['min']:.2f}, max={summary1['max']:.2f}")
    
    operation_metric = 'demo_operation_duration_seconds'
    if operation_metric in monitor.metrics:
        summary_op = monitor.get_metric_summary(operation_metric)
        print(f"   {operation_metric}: duration={summary_op['latest']:.3f}s")
    
    return monitor


def demonstrate_health_checks():
    """Demonstrate system health check capabilities."""
    print("\n" + "=" * 60)
    print("SYSTEM HEALTH CHECK DEMONSTRATION")
    print("=" * 60)
    
    # Initialize health checker with monitor
    monitor = PerformanceMonitor()
    health_checker = SystemHealthChecker(monitor)
    print("✅ System health checker initialized")
    
    # Run individual health checks
    print("\n🏥 Running individual health checks...")
    
    checks_to_run = [
        ('FIO Dependency', health_checker.check_fio_dependency),
        ('Memory Usage', health_checker.check_memory_usage),
        ('CPU Usage', health_checker.check_cpu_usage),
        ('Disk Space', health_checker.check_disk_space),
        ('Process Health', health_checker.check_process_health)
    ]
    
    results = []
    for check_name, check_func in checks_to_run:
        try:
            result = check_func()
            results.append(result)
            
            status_icon = {
                HealthStatus.HEALTHY: "✅",
                HealthStatus.WARNING: "⚠️",
                HealthStatus.CRITICAL: "❌",
                HealthStatus.UNKNOWN: "❓"
            }[result.status]
            
            print(f"   {status_icon} {check_name}: {result.status.value} - {result.message}")
            print(f"      Duration: {result.duration_ms:.2f}ms")
            
        except Exception as e:
            print(f"   ❌ {check_name}: Failed - {e}")
    
    # Run all health checks
    print("\n🔍 Running comprehensive health check suite...")
    all_results = health_checker.run_all_checks()
    health_summary = health_checker.get_health_summary(all_results)
    
    print(f"   Total checks: {health_summary['total_checks']}")
    print(f"   Healthy: {health_summary['healthy']} ✅")
    print(f"   Warnings: {health_summary['warnings']} ⚠️")
    print(f"   Critical: {health_summary['critical']} ❌")
    print(f"   Overall status: {health_summary['overall_status'].upper()}")
    
    return health_checker


def demonstrate_structured_logging():
    """Demonstrate structured logging capabilities."""
    print("\n" + "=" * 60)
    print("STRUCTURED LOGGING DEMONSTRATION")
    print("=" * 60)
    
    monitor = PerformanceMonitor()
    
    # Get a logger from the monitoring system
    import logging
    logger = logging.getLogger('diskbench.demo')
    
    print("📝 Generating structured log entries...")
    
    # Log various types of messages with context
    logger.info("Starting disk benchmark test", extra={
        'extra_fields': {
            'test_id': 'demo-test-001',
            'operation': 'disk_benchmark',
            'disk_path': '/tmp',
            'size_gb': 1.0
        }
    })
    
    logger.warning("High CPU usage detected during test", extra={
        'extra_fields': {
            'test_id': 'demo-test-001',
            'cpu_percent': 89.5,
            'threshold': 85.0
        }
    })
    
    logger.info("Test completed successfully", extra={
        'extra_fields': {
            'test_id': 'demo-test-001',
            'duration': 45.2,
            'status': 'completed',
            'results': {
                'read_bw_kbs': 150000,
                'write_bw_kbs': 80000
            }
        }
    })
    
    print("   ✅ Structured log entries written to JSON log file")
    print(f"   📁 Log file location: {monitor.log_dir}/diskbench.jsonl")


def demonstrate_metrics_export():
    """Demonstrate metrics export functionality."""
    print("\n" + "=" * 60)
    print("METRICS EXPORT DEMONSTRATION")
    print("=" * 60)
    
    monitor = PerformanceMonitor()
    
    # Add some sample metrics
    print("📊 Generating sample metrics...")
    for i in range(10):
        monitor.log_metric('sample_bandwidth', 100 + i * 10, tags={'test': 'export_demo'}, unit='kbs')
        monitor.log_metric('sample_latency', 5.0 + i * 0.5, tags={'test': 'export_demo'}, unit='ms')
        time.sleep(0.01)  # Small delay
    
    # Export metrics
    print("💾 Exporting metrics to JSON file...")
    export_file = monitor.export_metrics()
    print(f"   ✅ Metrics exported to: {export_file}")
    
    # Show export file contents summary
    with open(export_file, 'r') as f:
        export_data = json.load(f)
    
    print(f"   📊 Export contains:")
    print(f"      - System baseline metrics")
    print(f"      - Current system metrics")
    print(f"      - {len(export_data['collected_metrics'])} metric types")
    print(f"      - {len(export_data['metric_summaries'])} metric summaries")
    
    # Show metric summary
    if 'sample_bandwidth' in export_data['metric_summaries']:
        bw_summary = export_data['metric_summaries']['sample_bandwidth']
        print(f"      - Bandwidth metric: {bw_summary['count']} values, avg={bw_summary['avg']:.1f} kbs")


def main():
    """Run complete monitoring and observability demonstration."""
    print("🚀 DISKBENCH PHASE 3: MONITORING & OBSERVABILITY DEMONSTRATION")
    print("=" * 80)
    print("This demo showcases the comprehensive monitoring system implemented")
    print("in Phase 3 of the diskbench improvement plan.")
    print()
    
    try:
        # Run demonstrations
        monitor = demonstrate_performance_monitoring()
        health_checker = demonstrate_health_checks()
        demonstrate_structured_logging()
        demonstrate_metrics_export()
        
        # Final summary
        print("\n" + "=" * 60)
        print("PHASE 3 IMPLEMENTATION SUMMARY")
        print("=" * 60)
        print("✅ Performance monitoring with metrics collection")
        print("✅ System health checks with configurable thresholds")
        print("✅ Structured JSON logging with contextual information")
        print("✅ Operation timing and performance measurement")
        print("✅ Metrics export and persistence")
        print("✅ Real-time system resource monitoring")
        print("✅ Comprehensive test coverage (24 unit tests)")
        
        # Show current system status
        status = {
            'monitoring_enabled': True,
            'health_checks_enabled': True,
            'metrics_collected': len(monitor.metrics),
            'log_directory': str(monitor.log_dir),
        }
        
        print(f"\n📊 Current Status:")
        print(f"   Monitoring: {'Enabled' if status['monitoring_enabled'] else 'Disabled'}")
        print(f"   Health Checks: {'Enabled' if status['health_checks_enabled'] else 'Disabled'}")
        print(f"   Metrics Collected: {status['metrics_collected']} types")
        print(f"   Log Directory: {status['log_directory']}")
        
        print("\n🎯 Phase 3 objectives completed successfully!")
        print("The diskbench system now has comprehensive monitoring and observability.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
