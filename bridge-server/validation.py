"""Input validation helpers and security imports for the bridge server.

Contains regex constants, parameter limits, sanitization, and re-exports
of diskbench security utilities.
"""

import os
import re
import sys

# --- Path setup: ensure diskbench is importable ---
_base_dir = os.path.dirname(__file__)
_meipass = getattr(sys, '_MEIPASS', None)
_possible_diskbench_paths = [
    os.path.join(_base_dir, '..', 'diskbench'),  # source checkout
]
if _meipass:
    _possible_diskbench_paths.insert(0, os.path.join(_meipass, 'diskbench'))
for _p in _possible_diskbench_paths:
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)
        break

_repo_root = os.path.abspath(os.path.join(_base_dir, '..'))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

# Re-export security utilities (tests patch these via bridge.validate_disk_path etc.)
from diskbench.utils.security import (
    validate_disk_path,
    is_system_path,
    check_available_space,
)

# --- Regex constants ---

_BLOCK_SIZE_RE = re.compile(r'^\d+[kKmMgG]$')
_RATE_RE = re.compile(r'^\d+[kKmMgG]?$')

_PARAM_LIMITS = {
    'duration': (1, 43200),       # 1s - 12h
    'numjobs': (1, 16),
    'iodepth': (1, 256),
    'rw_mix': (0, 100),
}


def _sanitize_error(exc: Exception) -> str:
    """Return a generic error message without leaking system paths."""
    return f"Internal error: {type(exc).__name__}"


def _validate_custom_fio_params(params: dict) -> None:
    """Validate custom FIO parameters. Raises ValueError on bad input."""
    for key, (lo, hi) in _PARAM_LIMITS.items():
        raw = params.get(key)
        if raw is not None:
            try:
                val = int(raw)
            except (TypeError, ValueError):
                raise ValueError(f"Parameter '{key}' must be an integer")
            if not (lo <= val <= hi):
                raise ValueError(f"Parameter '{key}' must be between {lo} and {hi}")

    bs = params.get('block_size', '1M')
    if not _BLOCK_SIZE_RE.match(str(bs)):
        raise ValueError(
            f"Invalid block_size '{bs}'. Must match pattern like '4k', '1M', '2G'."
        )

    rate = params.get('target_rate', '')
    if rate and not _RATE_RE.match(str(rate)):
        raise ValueError(
            f"Invalid target_rate '{rate}'. Must match pattern like '500M', '1G'."
        )
