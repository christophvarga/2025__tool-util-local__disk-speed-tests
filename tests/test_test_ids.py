"""Unit tests for diskbench.core.test_ids
Version 1.0

Tests for backward-compatibility of enumerated test IDs

Intended for pytest runner.
"""

import pytest
from diskbench.core.test_ids import TestId


@pytest.mark.parametrize("alias, expected", [
    ("quick_max_mix", TestId.QUICK_MAX_MIX),
    ("quick_max_speed", TestId.QUICK_MAX_MIX),
    ("prores_422_real", TestId.PRORES_422_REAL),
    ("qlab_prores_422_show", TestId.PRORES_422_REAL),
    ("prores_422_hq_real", TestId.PRORES_422_HQ_REAL),
    ("qlab_prores_hq_show", TestId.PRORES_422_HQ_REAL),
    ("thermal_maximum", TestId.THERMAL_MAXIMUM),
    ("max_sustained", TestId.THERMAL_MAXIMUM),
])
def test_from_legacy(alias, expected):
    assert TestId.from_legacy(alias) is expected


@pytest.mark.parametrize("invalid_alias", [
    "unknown_test_id",
    "random_alias",
    "max_power",
])
def test_from_legacy_invalid(invalid_alias):
    with pytest.raises(KeyError):
        TestId.from_legacy(invalid_alias)

