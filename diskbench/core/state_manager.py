"""
SQLite-based state management for robust test persistence and recovery.

Provides atomic transactions, proper indexing, and recovery mechanisms
for tracking test execution state across server restarts.
"""
import sqlite3
import json
import os
import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path


class StateManager:
    """Robust state management with SQLite for test persistence."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize state manager with SQLite database.
        
        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        if db_path is None:
            # Default to memory-bank directory for consistency with existing JSON state
            db_dir = Path("memory-bank")
            db_dir.mkdir(exist_ok=True)
            self.db_path = str(db_dir / "diskbench_state.db")
        else:
            self.db_path = db_path
            
        self.logger = logging.getLogger(__name__)
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema with proper indexes."""
        with self._db() as conn:
            # Test runs table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS test_runs (
                    id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    test_type TEXT NOT NULL,
                    disk_path TEXT NOT NULL,
                    size_gb INTEGER NOT NULL,
                    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP NULL,
                    pid INTEGER NULL,
                    result_json TEXT NULL,
                    error_message TEXT NULL,
                    metadata_json TEXT NULL,
                    estimated_duration INTEGER DEFAULT 0,
                    output_file TEXT NULL
                )
            ''')
            
            # Test metrics table for detailed performance tracking
            conn.execute('''
                CREATE TABLE IF NOT EXISTS test_metrics (
                    test_id TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    metric_unit TEXT NULL,
                    FOREIGN KEY (test_id) REFERENCES test_runs(id)
                )
            ''')
            
            # Process tracking table for orphaned process recovery
            conn.execute('''
                CREATE TABLE IF NOT EXISTS process_tracking (
                    test_id TEXT NOT NULL,
                    pid INTEGER NOT NULL,
                    pgid INTEGER NULL,
                    command TEXT NULL,
                    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    status TEXT NOT NULL DEFAULT 'running',
                    PRIMARY KEY (test_id, pid),
                    FOREIGN KEY (test_id) REFERENCES test_runs(id)
                )
            ''')
            
            # Create indexes for performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_test_runs_status ON test_runs(status)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_test_runs_started ON test_runs(started_at)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_test_metrics_test_id ON test_metrics(test_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_process_tracking_status ON process_tracking(status)')
            
            self.logger.info(f"State database initialized: {self.db_path}")
    
    @contextmanager
    def _db(self):
        """Database connection context manager with proper error handling."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def save_test_start(self, test_id: str, test_info: Dict[str, Any]) -> bool:
        """
        Save test start with atomic transaction.
        
        Args:
            test_id: Unique test identifier
            test_info: Test information dictionary
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with self._db() as conn:
                # Insert test run
                conn.execute('''
                    INSERT INTO test_runs 
                    (id, status, test_type, disk_path, size_gb, pid, metadata_json, 
                     estimated_duration, output_file)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    test_id,
                    'running',
                    test_info.get('diskbench_test_type', 'unknown'),
                    test_info.get('params', {}).get('disk_path', ''),
                    test_info.get('params', {}).get('size_gb', 0),
                    test_info.get('pid'),
                    json.dumps(test_info.get('params', {})),
                    test_info.get('estimated_duration', 0),
                    test_info.get('output_file', '')
                ))
                
                # Track process if PID is available
                if test_info.get('pid'):
                    conn.execute('''
                        INSERT INTO process_tracking (test_id, pid, command)
                        VALUES (?, ?, ?)
                    ''', (
                        test_id,
                        test_info['pid'],
                        test_info.get('command', '')
                    ))
                
                self.logger.info(f"Test start saved: {test_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to save test start {test_id}: {e}")
            return False
    
    def update_test_status(self, test_id: str, status: str, 
                          result_data: Optional[Dict[str, Any]] = None,
                          error_message: Optional[str] = None) -> bool:
        """
        Update test status with optional result data.
        
        Args:
            test_id: Test identifier
            status: New status ('running', 'completed', 'failed', 'stopped')
            result_data: Optional test results
            error_message: Optional error message
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            with self._db() as conn:
                if status in ['completed', 'failed', 'stopped']:
                    # Mark as completed with timestamp
                    conn.execute('''
                        UPDATE test_runs 
                        SET status = ?, completed_at = CURRENT_TIMESTAMP, 
                            result_json = ?, error_message = ?
                        WHERE id = ?
                    ''', (
                        status,
                        json.dumps(result_data) if result_data else None,
                        error_message,
                        test_id
                    ))
                else:
                    # Update status only
                    conn.execute('''
                        UPDATE test_runs 
                        SET status = ?, error_message = ?
                        WHERE id = ?
                    ''', (status, error_message, test_id))
                
                # Update process tracking
                conn.execute('''
                    UPDATE process_tracking 
                    SET status = ?
                    WHERE test_id = ?
                ''', (status, test_id))
                
                self.logger.info(f"Test status updated: {test_id} -> {status}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to update test status {test_id}: {e}")
            return False
    
    def get_running_tests(self) -> List[Dict[str, Any]]:
        """Get all currently running tests."""
        try:
            with self._db() as conn:
                cursor = conn.execute('''
                    SELECT * FROM test_runs 
                    WHERE status = 'running' 
                    ORDER BY started_at DESC
                ''')
                
                tests = []
                for row in cursor:
                    test_data = dict(row)
                    # Parse JSON fields
                    if test_data['metadata_json']:
                        test_data['params'] = json.loads(test_data['metadata_json'])
                    if test_data['result_json']:
                        test_data['result'] = json.loads(test_data['result_json'])
                    tests.append(test_data)
                
                return tests
                
        except Exception as e:
            self.logger.error(f"Failed to get running tests: {e}")
            return []
    
    def recover_orphaned_tests(self) -> List[Dict[str, Any]]:
        """
        Recover tests from previous session that were running.
        
        Returns:
            List of test data for orphaned tests
        """
        try:
            with self._db() as conn:
                # Find tests that were running but started more than 1 hour ago
                # These are likely orphaned from a previous session
                cursor = conn.execute('''
                    SELECT tr.*, pt.pid, pt.pgid 
                    FROM test_runs tr
                    LEFT JOIN process_tracking pt ON tr.id = pt.test_id
                    WHERE tr.status = 'running' 
                    AND tr.started_at < datetime('now', '-1 hour')
                    ORDER BY tr.started_at DESC
                ''')
                
                orphaned = []
                for row in cursor:
                    test_data = dict(row)
                    
                    # Check if process still exists
                    if test_data['pid']:
                        if self._process_exists(test_data['pid']):
                            # Process still running - can potentially reconnect
                            test_data['recoverable'] = True
                        else:
                            # Process gone - mark as disconnected
                            self.update_test_status(test_data['id'], 'failed', 
                                                   error_message='Process terminated unexpectedly during server restart')
                            test_data['recoverable'] = False
                    else:
                        # No PID tracked - mark as unknown
                        self.update_test_status(test_data['id'], 'failed',
                                               error_message='Test status unknown after server restart')
                        test_data['recoverable'] = False
                    
                    orphaned.append(test_data)
                
                if orphaned:
                    self.logger.warning(f"Recovered {len(orphaned)} orphaned tests")
                
                return orphaned
                
        except Exception as e:
            self.logger.error(f"Failed to recover orphaned tests: {e}")
            return []
    
    def cleanup_old_tests(self, days_old: int = 7) -> int:
        """
        Clean up old completed/failed tests older than specified days.
        
        Args:
            days_old: Number of days to keep tests
            
        Returns:
            Number of tests cleaned up
        """
        try:
            with self._db() as conn:
                # Clean up old test metrics first (foreign key constraint)
                conn.execute('''
                    DELETE FROM test_metrics 
                    WHERE test_id IN (
                        SELECT id FROM test_runs 
                        WHERE status IN ('completed', 'failed', 'stopped')
                        AND completed_at < datetime('now', '-{} days')
                    )
                '''.format(days_old))
                
                # Clean up old process tracking
                conn.execute('''
                    DELETE FROM process_tracking 
                    WHERE test_id IN (
                        SELECT id FROM test_runs 
                        WHERE status IN ('completed', 'failed', 'stopped')
                        AND completed_at < datetime('now', '-{} days')
                    )
                '''.format(days_old))
                
                # Clean up old test runs
                cursor = conn.execute('''
                    DELETE FROM test_runs 
                    WHERE status IN ('completed', 'failed', 'stopped')
                    AND completed_at < datetime('now', '-{} days')
                '''.format(days_old))
                
                cleaned_count = cursor.rowcount
                if cleaned_count > 0:
                    self.logger.info(f"Cleaned up {cleaned_count} old tests")
                
                return cleaned_count
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old tests: {e}")
            return 0
    
    def get_test_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get test history with results."""
        try:
            with self._db() as conn:
                cursor = conn.execute('''
                    SELECT * FROM test_runs 
                    WHERE status IN ('completed', 'failed', 'stopped')
                    ORDER BY completed_at DESC 
                    LIMIT ?
                ''', (limit,))
                
                history = []
                for row in cursor:
                    test_data = dict(row)
                    # Parse JSON fields
                    if test_data['metadata_json']:
                        test_data['params'] = json.loads(test_data['metadata_json'])
                    if test_data['result_json']:
                        test_data['result'] = json.loads(test_data['result_json'])
                    history.append(test_data)
                
                return history
                
        except Exception as e:
            self.logger.error(f"Failed to get test history: {e}")
            return []
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics for monitoring."""
        try:
            with self._db() as conn:
                stats = {}
                
                # Count by status
                cursor = conn.execute('''
                    SELECT status, COUNT(*) as count 
                    FROM test_runs 
                    GROUP BY status
                ''')
                stats['test_counts'] = dict(cursor.fetchall())
                
                # Total tests
                cursor = conn.execute('SELECT COUNT(*) FROM test_runs')
                stats['total_tests'] = cursor.fetchone()[0]
                
                # Database file size
                if os.path.exists(self.db_path):
                    stats['db_size_bytes'] = os.path.getsize(self.db_path)
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}")
            return {}
    
    def _process_exists(self, pid: int) -> bool:
        """Check if process with given PID exists."""
        try:
            os.kill(pid, 0)  # Send signal 0 (no-op) to check if process exists
            return True
        except (OSError, ProcessLookupError):
            return False
