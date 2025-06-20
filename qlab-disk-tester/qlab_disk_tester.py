# qlab_disk_tester.py

import os
import sys
import subprocess
import json
import time

import os
import shutil
import platform

# Import our custom modules
from lib.disk_detector import DiskDetector
from lib.fio_engine import FioEngine
from lib.qlab_analyzer import QLabAnalyzer
from lib.report_generator import ReportGenerator
from lib.binary_manager import BinaryManager
from lib.live_monitor import LiveMonitor

# ANSI escape codes for colors
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_colored(text, color):
    print(f"{color}{text}{Colors.ENDC}")

def main():
    print_colored(f"{Colors.HEADER}{Colors.BOLD}QLab Disk Performance Tester{Colors.ENDC}", Colors.HEADER)
    print_colored(f"{Colors.OKBLUE}Professional Video Storage Testing{Colors.ENDC}", Colors.OKBLUE)
    print("\nInitializing system...\n")

    # 1. System Check and fio Installation Verification
    print_colored("Checking system compatibility and fio installation...", Colors.OKCYAN)
    
    # Get fio path from bundled binary or system using BinaryManager
    binary_manager = BinaryManager()
    is_available, fio_path, source_type = binary_manager.check_fio_availability()
    
    if not is_available:
        print_colored(f"{Colors.FAIL}fio binary not found. Please run install.sh first.{Colors.ENDC}", Colors.FAIL)
        binary_manager.print_installation_instructions()
        sys.exit(1)
    
    print_colored(f"System check complete. fio found: {fio_path}", Colors.OKGREEN)
    
    # Get fio version
    version = binary_manager.get_fio_version(fio_path)
    print_colored(f"Version: {version}", Colors.OKGREEN)

    # 2. Storage Device Detection
    print_colored("\nDetecting available storage devices (>300GB)...", Colors.OKCYAN)
    detector = DiskDetector(min_capacity_gb=300)
    drives = detector.get_large_drives()

    selected_drive = None
    
    if drives:
        print_colored("Detected large drives:", Colors.OKGREEN)
        for i, drive in enumerate(drives):
            drive_type = drive.get('Type', 'Unknown')
            source = drive.get('Source', 'unknown')
            print(f"  {i+1}. {Colors.BOLD}{drive['Name']}{Colors.ENDC} ({drive['Mount Point']}) - {drive.get('Free', 'Unknown')} free of {drive['Capacity']}")
            print(f"     Device: {drive['Device Name']} (Type: {drive_type}, Source: {source})")
        
        print(f"  {len(drives)+1}. {Colors.BOLD}Show More Volumes{Colors.ENDC} - List all mounted volumes")
        print(f"  {len(drives)+2}. {Colors.BOLD}Manual Path Entry{Colors.ENDC} - Enter a custom path")
        
        while selected_drive is None:
            try:
                choice = input(f"\n{Colors.OKBLUE}Select a drive by number: {Colors.ENDC}")
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(drives):
                    selected_drive = drives[choice_idx]
                elif choice_idx == len(drives):  # Show more volumes option
                    print_colored("\nShowing all mounted volumes:", Colors.OKCYAN)
                    volumes = detector.get_volume_list()
                    if volumes:
                        for i, vol in enumerate(volumes):
                            print(f"  {i+1}. {Colors.BOLD}{vol['Name']}{Colors.ENDC} ({vol['Mount Point']}) - {vol['Free']} free of {vol['Capacity']}")
                        
                        vol_choice = input(f"\n{Colors.OKBLUE}Select a volume by number (or 0 to go back): {Colors.ENDC}")
                        try:
                            vol_idx = int(vol_choice) - 1
                            if vol_idx == -1:  # Go back
                                continue
                            elif 0 <= vol_idx < len(volumes):
                                selected_drive = volumes[vol_idx]
                            else:
                                print_colored(f"{Colors.WARNING}Invalid choice.{Colors.ENDC}", Colors.WARNING)
                                continue
                        except ValueError:
                            print_colored(f"{Colors.WARNING}Invalid input.{Colors.ENDC}", Colors.WARNING)
                            continue
                    else:
                        print_colored("No suitable volumes found.", Colors.WARNING)
                        continue
                elif choice_idx == len(drives) + 1:  # Manual entry option
                    manual_path = input(f"{Colors.OKBLUE}Enter the full path to test (e.g., /Volumes/MyDrive): {Colors.ENDC}")
                    is_valid, message = detector.validate_manual_path(manual_path)
                    if is_valid:
                        selected_drive = {
                            'Name': os.path.basename(manual_path) or 'Manual Path',
                            'Mount Point': manual_path,
                            'Capacity': 'Unknown',
                            'Free': message.split()[-2] + ' GB',  # Extract free space from validation message
                            'Device Name': 'Manual Entry',
                            'Internal': 'Unknown',
                            'Protocol': 'Unknown',
                            'Type': 'Manual',
                            'Source': 'manual'
                        }
                        print_colored(f"Manual path validated: {message}", Colors.OKGREEN)
                    else:
                        print_colored(f"{Colors.FAIL}Invalid path: {message}{Colors.ENDC}", Colors.FAIL)
                        continue
                else:
                    print_colored(f"{Colors.WARNING}Invalid choice. Please enter a number between 1 and {len(drives)+1}.{Colors.ENDC}", Colors.WARNING)
            except ValueError:
                print_colored(f"{Colors.WARNING}Invalid input. Please enter a number.{Colors.ENDC}", Colors.WARNING)
    else:
        # No drives detected - force manual entry
        print_colored(f"{Colors.WARNING}No large drives (>300GB) detected automatically.{Colors.ENDC}", Colors.WARNING)
        print_colored("Please enter a path manually:", Colors.OKCYAN)
        
        while selected_drive is None:
            manual_path = input(f"{Colors.OKBLUE}Enter the full path to test (e.g., /Volumes/MyDrive or /tmp): {Colors.ENDC}")
            if not manual_path:
                print_colored(f"{Colors.FAIL}No path entered. Exiting.{Colors.ENDC}", Colors.FAIL)
                sys.exit(1)
            
            is_valid, message = detector.validate_manual_path(manual_path)
            if is_valid:
                selected_drive = {
                    'Name': os.path.basename(manual_path) or 'Manual Path',
                    'Mount Point': manual_path,
                    'Capacity': 'Unknown',
                    'Free': message.split()[-2] + ' GB',  # Extract free space from validation message
                    'Device Name': 'Manual Entry',
                    'Internal': 'Unknown',
                    'Protocol': 'Unknown',
                    'Type': 'Manual',
                    'Source': 'manual'
                }
                print_colored(f"Manual path validated: {message}", Colors.OKGREEN)
            else:
                print_colored(f"{Colors.FAIL}Invalid path: {message}{Colors.ENDC}", Colors.FAIL)
                retry = input(f"{Colors.OKBLUE}Try again? (y/n): {Colors.ENDC}").lower()
                if retry != 'y':
                    print_colored("Exiting.", Colors.FAIL)
                    sys.exit(1)
    
    print_colored(f"\nSelected Drive: {Colors.BOLD}{selected_drive['Name']}{Colors.ENDC} ({selected_drive['Mount Point']})", Colors.OKGREEN)

    # 3. Test Mode Selection
    print_colored("\nSelect a test mode:", Colors.OKCYAN)
    test_modes = {
        "0": {"name": "Setup Check (30s)", "mode": "setup_check", "description": "30s - Quick test to verify basic functionality."},
        "1": {"name": "QLab Show-Pattern Test (2.5h)", "mode": "qlab_show_pattern", "description": "2.5h - Realistic show simulation: Warmup → Normal Show → Finale with thermal monitoring."},
        "2": {"name": "Max Sustained Performance (2h)", "mode": "max_sustained", "description": "2h - Maximum sustained throughput test for thermal stability."}
    }

    for key, value in test_modes.items():
        print(f"  {key}. {Colors.BOLD}{value['name']}{Colors.ENDC}: {value['description']}")

    selected_mode = None
    while selected_mode is None:
        try:
            choice = input(f"\n{Colors.OKBLUE}Enter test mode number: {Colors.ENDC}")
            if choice in test_modes:
                selected_mode = test_modes[choice]
            else:
                print_colored(f"{Colors.WARNING}Invalid choice. Please enter a number between 1 and {len(test_modes)}.{Colors.ENDC}", Colors.WARNING)
        except ValueError:
            print_colored(f"{Colors.WARNING}Invalid input. Please enter a number.{Colors.ENDC}", Colors.WARNING)
    
    print_colored(f"\nSelected Test Mode: {Colors.BOLD}{selected_mode['name']}{Colors.ENDC}", Colors.OKGREEN)

    # 4. fio Test Execution
    # Diese Zeile wurde entfernt, da sie die In-Place-Updates des Live-Monitors stört.
    fio_engine = FioEngine(fio_path=fio_path)
    
    # Determine test size based on selected mode and available free space
    def parse_size_to_gb(size_str):
        """Parse size string like '500 GB' to float in GB."""
        if not size_str or size_str == 'Unknown':
            return 0
        size_str = size_str.replace(',', '').strip()
        parts = size_str.split()
        if len(parts) >= 2:
            try:
                value = float(parts[0])
                unit = parts[1].upper()
                if unit in ['TB', 'TERABYTES']:
                    return value * 1024
                elif unit in ['GB', 'GIGABYTES']:
                    return value
                elif unit in ['MB', 'MEGABYTES']:
                    return value / 1024
            except ValueError:
                pass
        return 0
    
    free_space_gb = parse_size_to_gb(selected_drive['Free'])
    
    # Calculate safe test sizes (max 25% of free space, with mode-specific minimums)
    max_safe_size = max(1, free_space_gb * 0.25)  # 25% of free space, minimum 1GB
    
    # Default test sizes for new test modes
    default_sizes = {
        "setup_check": 0.1,          # 100MB for quick setup check
        "qlab_show_pattern": 50,     # 50GB for realistic show simulation
        "max_sustained": 100         # 100GB for sustained performance
    }
    
    desired_size = default_sizes.get(selected_mode['mode'], 20)
    test_size_gb = min(desired_size, max_safe_size)
    
    # Warning BEFORE starting Live-Monitor to avoid interrupting \r updates
    if test_size_gb < desired_size:
        print_colored(f"{Colors.WARNING}Warning: Insufficient free space for optimal test size.{Colors.ENDC}", Colors.WARNING)
        print_colored(f"Desired: {desired_size}GB, Available: {free_space_gb:.1f}GB, Using: {test_size_gb:.1f}GB", Colors.WARNING)
    
    # Initialize live monitor for ALL tests AFTER all prints
    monitor = None
    if selected_mode['mode'] in ['setup_check', 'qlab_show_pattern', 'max_sustained']:
        # Die folgenden Print-Anweisungen wurden entfernt, da sie die In-Place-Updates des Live-Monitors stören.
        # Die relevanten Informationen werden jetzt direkt in der Live-Monitor-Zeile angezeigt.
        monitor = LiveMonitor()
        monitor.start_monitoring()
        time.sleep(1)  # Kurze Pause für den Monitor-Start

    try:
        fio_results = fio_engine.execute_fio_test(selected_mode['mode'], selected_drive['Mount Point'], test_size_gb, monitor)
    except KeyboardInterrupt:
        print_colored(f"\n\n{Colors.WARNING}Test interrupted by user. Stopping safely...{Colors.ENDC}", Colors.WARNING)
        if monitor:
            monitor.stop_monitoring()
        sys.exit(0)
    finally:
        if monitor:
            monitor.stop_monitoring()
            print("\n🔴 Live monitoring stopped.")

    if fio_results:
        print_colored("fio test complete. Raw results (first job):", Colors.OKGREEN)
        # For now, just print the first job's results for verification
        print(json.dumps(fio_results[0], indent=2))
    else:
        print_colored(f"{Colors.FAIL}fio test failed or returned no results.{Colors.ENDC}", Colors.FAIL)
        sys.exit(1)

    # Clean up test files
    fio_engine.cleanup_test_files(selected_drive['Mount Point'])

    # 5. Results Analysis and Reporting
    print_colored("\nAnalyzing results and generating report...", Colors.OKCYAN)
    analyzer = QLabAnalyzer()
    analysis_results = analyzer.analyze_fio_results(fio_results)

    if analysis_results:
        reporter = ReportGenerator(Colors)
        reporter.generate_cli_report(analysis_results)
        reporter.export_json_results(analysis_results, fio_results, selected_drive, selected_mode)
    else:
        print_colored(f"{Colors.FAIL}Analysis failed or returned no results.{Colors.ENDC}", Colors.FAIL)

    print_colored(f"\n{Colors.OKGREEN}{Colors.BOLD}Testing complete!{Colors.ENDC}", Colors.OKGREEN)

# Functions removed - now using BinaryManager

if __name__ == "__main__":
    main()
