"""diskbench.core.test_ids
Version 1.0

Enum of canonical test identifiers used throughout diskbench.

When new test IDs are introduced, add them here together with eventual legacy
aliases to keep backward-compatibility intact.
"""

from __future__ import annotations
from enum import Enum
from typing import Dict


_legacy_mapping = {
    "quick_max_speed": "quick_max_mix",
    "qlab_prores_422_show": "prores_422_real",
    "qlab_prores_hq_show": "prores_422_hq_real",
    "max_sustained": "thermal_maximum",
}


class TestId(str, Enum):
    """Canonical identifiers for built-in diskbench tests."""

    QUICK_MAX_MIX = "quick_max_mix"
    PRORES_422_REAL = "prores_422_real"
    PRORES_422_HQ_REAL = "prores_422_hq_real"
    THERMAL_MAXIMUM = "thermal_maximum"

    # Make legacy mapping accessible from the enum
    legacy_aliases: Dict[str, str] = _legacy_mapping

    @classmethod
    def from_legacy(cls, value: str) -> "TestId":
        """Return the :class:`TestId` corresponding to *value*.

        Args:
            value: A test ID string, either a canonical value or a legacy alias.

        Returns:
            The corresponding TestId enum member.

        Raises:
            KeyError: If the test ID is not recognized.
        """
        try:
            return cls(value)  # Try direct lookup first
        except ValueError:
            pass

        # Try legacy lookup
        try:
            canonical = _legacy_mapping[value]
            return cls(canonical)
        except KeyError:
            known_ids = [member.value for member in cls]
            legacy_ids = list(_legacy_mapping.keys())
            raise KeyError(
                f"Unknown test id '{value}'. Known ids: {', '.join(known_ids)} "
                f"and legacy aliases: {', '.join(legacy_ids)}"
            )

