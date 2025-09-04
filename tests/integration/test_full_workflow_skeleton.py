import pytest

pytestmark = [pytest.mark.integration, pytest.mark.skip(reason="Skeleton – wird in Phase 1 weiter ausgearbeitet")] 

def test_full_workflow_skeleton():
    # Placeholder für End-to-End Test: Bridge ↔ diskbench ↔ FIO ↔ Parsing ↔ GUI
    assert True

