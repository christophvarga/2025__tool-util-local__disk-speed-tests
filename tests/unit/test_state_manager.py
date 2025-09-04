import sys
import tempfile
import os
from pathlib import Path
import pytest

DISKBENCH_DIR = Path(__file__).resolve().parents[2] / "diskbench"
if str(DISKBENCH_DIR) not in sys.path:
    sys.path.insert(0, str(DISKBENCH_DIR))

from core.state_manager import StateManager


@pytest.fixture
def state_manager():
    """Create a StateManager with temporary database."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
        temp_path = temp_db.name
    
    sm = StateManager(db_path=temp_path)
    yield sm
    
    # Cleanup
    try:
        os.unlink(temp_path)
    except FileNotFoundError:
        pass


def test_state_manager_init_creates_tables(state_manager):
    """Test that StateManager initializes database schema correctly."""
    stats = state_manager.get_database_stats()
    assert stats['total_tests'] == 0
    assert 'test_counts' in stats


def test_save_and_retrieve_test_start(state_manager):
    """Test saving and retrieving test start information."""
    test_info = {
        'diskbench_test_type': 'quick_max_mix',
        'params': {'disk_path': '/Volumes/Test', 'size_gb': 10},
        'estimated_duration': 300,
        'output_file': '/tmp/test.json',
        'pid': 1234
    }
    
    result = state_manager.save_test_start('test_123', test_info)
    assert result is True
    
    running_tests = state_manager.get_running_tests()
    assert len(running_tests) == 1
    assert running_tests[0]['id'] == 'test_123'
    assert running_tests[0]['status'] == 'running'
    assert running_tests[0]['test_type'] == 'quick_max_mix'
    assert running_tests[0]['pid'] == 1234


def test_update_test_status_completion(state_manager):
    """Test updating test status to completion with results."""
    # Start a test
    test_info = {
        'diskbench_test_type': 'thermal_maximum',
        'params': {'disk_path': '/Volumes/Test', 'size_gb': 5},
        'pid': 5678
    }
    state_manager.save_test_start('test_456', test_info)
    
    # Complete the test
    result_data = {'summary': {'total_read_bw': 1000, 'total_write_bw': 800}}
    success = state_manager.update_test_status('test_456', 'completed', result_data=result_data)
    assert success is True
    
    # Check no running tests
    running_tests = state_manager.get_running_tests()
    assert len(running_tests) == 0
    
    # Check history
    history = state_manager.get_test_history(limit=10)
    assert len(history) == 1
    assert history[0]['id'] == 'test_456'
    assert history[0]['status'] == 'completed'
    assert 'result' in history[0]
    assert history[0]['result']['summary']['total_read_bw'] == 1000


def test_recover_orphaned_tests_with_process_gone(state_manager, monkeypatch):
    """Test recovery of orphaned tests where process no longer exists."""
    # Mock _process_exists to return False (process gone)
    monkeypatch.setattr(state_manager, '_process_exists', lambda pid: False)
    
    # Manually insert an old running test (simulate server restart scenario)
    with state_manager._db() as conn:
        conn.execute('''
            INSERT INTO test_runs 
            (id, status, test_type, disk_path, size_gb, started_at, pid)
            VALUES (?, ?, ?, ?, ?, datetime('now', '-2 hours'), ?)
        ''', ('old_test', 'running', 'quick_max_mix', '/Volumes/Old', 1, 9999))
    
    orphaned = state_manager.recover_orphaned_tests()
    assert len(orphaned) == 1
    assert orphaned[0]['id'] == 'old_test'
    assert orphaned[0]['recoverable'] is False
    
    # Should be marked as failed now
    running_tests = state_manager.get_running_tests()
    assert len(running_tests) == 0


def test_cleanup_old_tests(state_manager):
    """Test cleanup of old completed tests."""
    # Create some old completed tests by manually inserting them
    with state_manager._db() as conn:
        # Old test (should be cleaned up)
        conn.execute('''
            INSERT INTO test_runs 
            (id, status, test_type, disk_path, size_gb, started_at, completed_at)
            VALUES (?, ?, ?, ?, ?, datetime('now', '-10 days'), datetime('now', '-10 days'))
        ''', ('old_completed', 'completed', 'quick_max_mix', '/Volumes/Test', 1))
        
        # Recent test (should not be cleaned up)
        conn.execute('''
            INSERT INTO test_runs 
            (id, status, test_type, disk_path, size_gb, started_at, completed_at)
            VALUES (?, ?, ?, ?, ?, datetime('now', '-1 day'), datetime('now', '-1 day'))
        ''', ('recent_completed', 'completed', 'quick_max_mix', '/Volumes/Test', 1))
    
    # Clean up tests older than 7 days
    cleaned_count = state_manager.cleanup_old_tests(days_old=7)
    assert cleaned_count == 1
    
    # Verify recent test still exists
    history = state_manager.get_test_history(limit=10)
    assert len(history) == 1
    assert history[0]['id'] == 'recent_completed'


def test_get_database_stats(state_manager):
    """Test database statistics collection."""
    # Add some test data
    test_info = {
        'diskbench_test_type': 'quick_max_mix',
        'params': {'disk_path': '/Volumes/Test', 'size_gb': 1}
    }
    state_manager.save_test_start('test_stats', test_info)
    state_manager.update_test_status('test_stats', 'completed')
    
    stats = state_manager.get_database_stats()
    assert stats['total_tests'] == 1
    assert 'test_counts' in stats
    assert stats['test_counts']['completed'] == 1
    assert 'db_size_bytes' in stats
    assert stats['db_size_bytes'] > 0
