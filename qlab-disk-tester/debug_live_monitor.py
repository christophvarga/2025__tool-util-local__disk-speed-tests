#!/usr/bin/env python3
"""
Debug-Script für Live-Monitoring
Testet alle Komponenten einzeln
"""

import sys
import time
from lib.live_monitor import LiveMonitor

def test_live_monitor():
    """Test Live-Monitor Schritt für Schritt."""
    print("🔍 Testing Live Monitor Components...")
    
    monitor = LiveMonitor()
    
    # Test 1: Initial data
    print(f"Initial data: {monitor.data}")
    
    # Test 2: System metrics update
    print("\n🔧 Testing system metrics update...")
    monitor._update_system_metrics()
    print(f"After metrics update: {monitor.data}")
    
    # Test 3: Temperature estimation
    print("\n🌡️ Testing temperature estimation...")
    temp = monitor._estimate_temp_from_thermal_state()
    print(f"Estimated temperature: {temp}°C")
    
    # Test 4: Status generation
    print("\n📊 Testing status generation...")
    status = monitor.get_live_status()
    print(f"Live status: {status}")
    
    # Test 5: Phase simulation
    print("\n🎯 Testing phase simulation...")
    monitor.start_monitoring()
    
    # Simuliere verschiedene Test-Phasen
    phases = [
        ("Show Prep - Warmup Phase", 10),
        ("Normal Show - Streaming Phase", 15),
        ("Show Finale - Peak Performance", 10)
    ]
    
    for phase_name, duration in phases:
        print(f"\n📋 Starting phase: {phase_name}")
        monitor.set_test_phase(phase_name, duration)
        
        # Reset den Status-Ausgabe-Zustand für neue Phase
        if hasattr(monitor, '_first_status_printed'):
            delattr(monitor, '_first_status_printed')
        
        # Zeige echte Live-Updates für diese Phase (same line updates)
        for i in range(5):
            monitor.print_live_status()  # In-place update
            time.sleep(1)
        
        # Nach der Phase: neue Zeile für saubere Trennung
        monitor.print_live_status(force_newline=True)
    
    monitor.stop_monitoring()
    print("\n✅ Live monitor test completed!")
    print("\n🎯 Expected behavior:")
    print("  • SSD temperature should vary based on simulated I/O load")
    print("  • CPU usage should change between phases")
    print("  • I/O rates should reflect phase requirements")
    print("  • Time counters should show elapsed/remaining time")
    print("  • Phase names should be descriptive and clear")

if __name__ == "__main__":
    test_live_monitor()