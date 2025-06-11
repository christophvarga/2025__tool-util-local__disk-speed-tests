#!/usr/bin/env python3
"""
Debug Script - exakte FIO Engine Sequenz nachbauen
"""

import time
import sys
import os

# Pfad zum lib Verzeichnis hinzufügen
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.live_monitor import LiveMonitor

def simulate_exact_fio_sequence():
    print("Debug: Exakte FIO Engine Sequenz...")
    print("")
    
    # Exakt wie in FIO Engine
    job_commands = [
        ["fake_job1"],
        ["fake_job2"]
    ]
    
    live_monitor = LiveMonitor()
    live_monitor.start_monitoring()
    
    def _get_phase_info(test_mode, phase_index):
        """Exakte Kopie der FIO Engine Funktion"""
        if test_mode == "setup_check":
            phases = [
                ("Setup Check - Read Test", 30),
                ("Setup Check - Write Test", 30)
            ]
        if phase_index < len(phases):
            return phases[phase_index]
        return f"Phase {phase_index + 1}", 300

    try:
        # Exakte Schleife aus FIO Engine
        for i, cmd_parts in enumerate(job_commands):
            # print(f"DEBUG: Starting job {i}: {cmd_parts}")  # Das IST das Problem!
            
            # Setze Phase-Information für Live-Monitoring
            if live_monitor:
                phase_name, phase_duration = _get_phase_info("setup_check", i)
                live_monitor.set_test_phase(phase_name, phase_duration)
                # Phase-Info wird im Live-Monitor angezeigt, kein extra Print nötig
            
            # Live monitoring während "fio" läuft
            if live_monitor:
                # Sofortiges erstes Update NUR für den ersten Job
                if i == 0:
                    live_monitor.print_live_status()
                last_update = time.time()
                
                # Simuliere job laufzeit
                for j in range(3):  # 3 Sekunden pro Job
                    current_time = time.time()
                    if current_time - last_update >= 1:  # Update jede Sekunde
                        live_monitor.print_live_status()  # In-place update
                        last_update = current_time
                    time.sleep(1)
        
        # Finale Newline erst nach ALLEN Jobs für saubere Trennung
        if live_monitor:
            live_monitor.print_live_status(force_newline=True)
            
    finally:
        live_monitor.stop_monitoring()
        print("Debug beendet.")

if __name__ == "__main__":
    simulate_exact_fio_sequence()