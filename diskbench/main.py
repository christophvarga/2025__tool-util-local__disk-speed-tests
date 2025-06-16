#!/usr/bin/env python3
"""
diskbench - QLab Disk Performance Testing Helper Binary

A standalone CLI tool for professional disk performance testing using FIO.
Designed to work with the QLab Disk Performance Tester web interface.

Usage:
    diskbench --test qlab_hq --disk /dev/disk1s1 --output results.json
    diskbench --list-disks --json
    diskbench --version --check-fio
"""

import sys
import os
import argparse
import json
import logging
from pathlib import Path

# Add the current directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import modules with error handling
try:
    from commands.test import TestCommand
    from commands.list_disks import ListDisksCommand
    from commands.validate import ValidateCommand
    from commands.setup import handle_detect_command, handle_install_command, handle_validate_command as handle_setup_validate_command
    from utils.logging import setup_logging
    from utils.security import validate_disk_path, sanitize_filename
    from utils.system_info import get_system_info
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all required modules are present in the diskbench directory")
    sys.exit(1)

__version__ = "1.0.0"

def create_parser():
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog='diskbench',
        description='QLab Disk Performance Testing Helper Binary',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  diskbench --test setup_check --disk /dev/disk1s1 --output results.json
  diskbench --test qlab_prores_hq --disk /dev/disk1s1 --size 10
  diskbench --custom-config ./my-pattern.fio --disk /dev/disk1s1
  diskbench --list-disks --json
  diskbench --version --check-fio
        """
    )
    
    # Main operation modes (mutually exclusive)
    operation_group = parser.add_mutually_exclusive_group(required=True)
    
    operation_group.add_argument(
        '--test',
        choices=['setup_check', 'qlab_prores_422', 'qlab_prores_hq', 'baseline_streaming', 
                'quick_max_speed', 'qlab_prores_422_show', 'qlab_prores_hq_show', 'max_sustained'],
        help='Run a built-in test pattern'
    )
    
    operation_group.add_argument(
        '--custom-config',
        type=str,
        metavar='FILE',
        help='Run a custom FIO configuration file'
    )
    
    operation_group.add_argument(
        '--list-disks',
        action='store_true',
        help='List available disks for testing'
    )
    
    operation_group.add_argument(
        '--version',
        action='store_true',
        help='Show version information'
    )
    
    operation_group.add_argument(
        '--validate',
        action='store_true',
        help='Validate system and FIO installation'
    )
    
    operation_group.add_argument(
        '--detect',
        action='store_true',
        help='Detect system status and FIO availability'
    )
    
    operation_group.add_argument(
        '--install',
        action='store_true',
        help='Install or fix FIO for macOS'
    )
    
    operation_group.add_argument(
        '--setup-validate',
        action='store_true',
        help='Run setup validation tests'
    )
    
    # Test execution options
    parser.add_argument(
        '--disk',
        type=str,
        metavar='PATH',
        help='Target disk path (e.g., /dev/disk1s1 or /Volumes/MyDisk)'
    )
    
    parser.add_argument(
        '--size',
        type=int,
        metavar='GB',
        default=10,
        help='Test file size in GB (default: 10)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        metavar='FILE',
        help='Output file for JSON results'
    )
    
    # Output format options
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results in JSON format'
    )
    
    parser.add_argument(
        '--progress',
        action='store_true',
        help='Show real-time progress updates'
    )
    
    # System options
    parser.add_argument(
        '--check-fio',
        action='store_true',
        help='Check FIO binary availability and version'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    return parser

def validate_arguments(args):
    """Validate command-line arguments and dependencies."""
    errors = []
    
    # Test operations require disk and output
    if args.test or args.custom_config:
        if not args.disk:
            errors.append("--disk is required for test operations")
        else:
            # Validate disk path
            if not validate_disk_path(args.disk):
                errors.append(f"Invalid or inaccessible disk path: {args.disk}")
        
        if not args.output:
            errors.append("--output is required for test operations")
        else:
            # Validate output path
            output_dir = os.path.dirname(os.path.abspath(args.output))
            if not os.path.exists(output_dir):
                errors.append(f"Output directory does not exist: {output_dir}")
            elif not os.access(output_dir, os.W_OK):
                errors.append(f"Output directory is not writable: {output_dir}")
    
    # Custom config file validation
    if args.custom_config:
        if not os.path.exists(args.custom_config):
            errors.append(f"Custom config file not found: {args.custom_config}")
        elif not os.access(args.custom_config, os.R_OK):
            errors.append(f"Custom config file is not readable: {args.custom_config}")
    
    # Size validation
    if args.size and (args.size < 1 or args.size > 1000):
        errors.append("Test size must be between 1 and 1000 GB")
    
    return errors

def main():
    """Main entry point for the diskbench CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else (logging.INFO if args.verbose else logging.WARNING)
    setup_logging(log_level)
    logger = logging.getLogger(__name__)
    
    try:
        # Handle version command
        if args.version:
            version_info = {
                'diskbench_version': __version__,
                'python_version': sys.version,
                'system_info': get_system_info()
            }
            
            if args.check_fio:
                from core.fio_runner import FioRunner
                fio_runner = FioRunner()
                version_info['fio_status'] = fio_runner.get_fio_status()
            
            if args.json:
                print(json.dumps(version_info, indent=2))
            else:
                print(f"diskbench version {__version__}")
                if args.check_fio:
                    fio_status = version_info['fio_status']
                    if fio_status['available']:
                        print(f"FIO: {fio_status['version']} at {fio_status['path']}")
                    else:
                        print(f"FIO: Not available - {fio_status['error']}")
            return 0
        
        # Validate arguments
        validation_errors = validate_arguments(args)
        if validation_errors:
            logger.error("Argument validation failed:")
            for error in validation_errors:
                logger.error(f"  - {error}")
            return 1
        
        # Handle list-disks command
        if args.list_disks:
            list_cmd = ListDisksCommand()
            result = list_cmd.execute(json_output=args.json)
            if result is None:
                return 1
            
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print("Available disks:")
                for disk in result.get('disks', []):
                    print(f"  {disk['device']} - {disk['name']} ({disk['size']}, {disk['type']})")
            return 0
        
        # Handle validate command
        if args.validate:
            validate_cmd = ValidateCommand()
            result = validate_cmd.execute(json_output=args.json)
            if result is None:
                return 1
            
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print("System validation:")
                for check, status in result.get('checks', {}).items():
                    status_icon = "✅" if status['passed'] else "❌"
                    print(f"  {status_icon} {check}: {status['message']}")
            
            return 0 if result.get('overall_status') == 'passed' else 1
        
        # Handle setup commands
        if args.detect:
            return handle_detect_command(args)
        
        if args.install:
            return handle_install_command(args)
        
        if args.setup_validate:
            return handle_setup_validate_command(args)
        
        # Handle test commands
        if args.test or args.custom_config:
            test_cmd = TestCommand()
            
            # Prepare test parameters
            test_params = {
                'disk_path': args.disk,
                'test_size_gb': args.size,
                'output_file': args.output,
                'show_progress': args.progress,
                'json_output': args.json
            }
            
            if args.test:
                test_params['test_mode'] = args.test
                result = test_cmd.execute_builtin_test(**test_params)
            else:
                test_params['config_file'] = args.custom_config
                result = test_cmd.execute_custom_test(**test_params)
            
            if result is None:
                logger.error("Test execution failed")
                return 1
            
            # Save results to output file
            try:
                with open(args.output, 'w') as f:
                    json.dump(result, f, indent=2)
                logger.info(f"Results saved to {args.output}")
            except Exception as e:
                logger.error(f"Failed to save results: {e}")
                return 1
            
            return 0
        
        # Should not reach here due to mutually exclusive group
        parser.print_help()
        return 1
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.debug:
            import traceback
            logger.error(traceback.format_exc())
        return 1

if __name__ == '__main__':
    sys.exit(main())
