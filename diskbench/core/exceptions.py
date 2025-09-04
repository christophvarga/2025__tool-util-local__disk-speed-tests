"""
Custom exceptions with detailed context for diskbench.

Provides structured error handling with context information and recovery hints
for better debugging and user feedback.
"""
from datetime import datetime
from typing import Dict, Any, Optional


class DiskBenchError(Exception):
    """Base exception with context and recovery hints."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, recovery_hint: Optional[str] = None):
        super().__init__(message)
        self.context = context or {}
        self.recovery_hint = recovery_hint
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON serialization."""
        return {
            'error_type': self.__class__.__name__,
            'message': str(self),
            'context': self.context,
            'recovery_hint': self.recovery_hint,
            'timestamp': self.timestamp
        }


class FIOExecutionError(DiskBenchError):
    """FIO execution failed."""
    
    def __init__(self, message: str, return_code: Optional[int] = None, 
                 stdout: Optional[str] = None, stderr: Optional[str] = None):
        context = {
            'return_code': return_code,
            'stdout': stdout[:500] if stdout else None,
            'stderr': stderr[:500] if stderr else None
        }
        recovery_hint = "Check FIO installation and parameters. Try running with --validate flag."
        super().__init__(message, context, recovery_hint)


class DiskNotAvailableError(DiskBenchError):
    """Target disk not available or accessible."""
    
    def __init__(self, disk_path: str, reason: str = ""):
        message = f"Disk not available: {disk_path}"
        if reason:
            message += f" ({reason})"
        
        context = {'disk_path': disk_path, 'reason': reason}
        recovery_hint = "Check disk path and permissions. Use --list-disks to see available options."
        super().__init__(message, context, recovery_hint)


class InsufficientSpaceError(DiskBenchError):
    """Not enough disk space for test."""
    
    def __init__(self, required_gb: float, available_gb: float, disk_path: str):
        message = f"Insufficient space: need {required_gb}GB, have {available_gb}GB available"
        context = {
            'required_gb': required_gb,
            'available_gb': available_gb,
            'disk_path': disk_path
        }
        recovery_hint = "Free up disk space or reduce test size with --size parameter."
        super().__init__(message, context, recovery_hint)


class InvalidTestConfigError(DiskBenchError):
    """Invalid test configuration or parameters."""
    
    def __init__(self, config_issue: str, test_id: Optional[str] = None):
        message = f"Invalid test configuration: {config_issue}"
        context = {'test_id': test_id, 'config_issue': config_issue}
        recovery_hint = "Check test parameters and configuration. Use --list-tests to see valid options."
        super().__init__(message, context, recovery_hint)


class JSONParsingError(DiskBenchError):
    """Failed to parse FIO JSON output."""
    
    def __init__(self, parse_error: str, line_no: Optional[int] = None, 
                 column_no: Optional[int] = None, content_preview: Optional[str] = None):
        message = f"JSON parsing failed: {parse_error}"
        context = {
            'parse_error': parse_error,
            'line_no': line_no,
            'column_no': column_no,
            'content_preview': content_preview[:200] if content_preview else None
        }
        recovery_hint = "FIO output may be corrupted. Try re-running the test or check FIO version."
        super().__init__(message, context, recovery_hint)
