#!/usr/bin/env python3
"""
QLab Disk Performance Tester - Communication Bridge Server

Thin entry-point that assembles DiskBenchBridge from mixins and
re-exports all public names so that ``import server as bridge``
continues to work unchanged.
"""

import logging
import subprocess  # noqa: F401  -- tests patch bridge.subprocess
import sys

# --- Module re-exports (used by tests via ``bridge.<name>``) ----------

from validation import (                    # noqa: F401
    _sanitize_error,
    _validate_custom_fio_params,
    _BLOCK_SIZE_RE,
    _RATE_RE,
    _PARAM_LIMITS,
    validate_disk_path,
    is_system_path,
    check_available_space,
)

from bridge_core import DiskBenchBridgeCore
from bridge_status import BridgeStatusMixin
from process_manager import ProcessManagerMixin
from test_control import TestControlMixin
from fio_utils import FioUtilsMixin
from fio_setup import FioSetupMixin

from http_handlers import (                 # noqa: F401
    BridgeRequestHandler,
    ThreadedHTTPServer,
    create_request_handler,
)


# --- Composite DiskBenchBridge class ----------------------------------

class DiskBenchBridge(
    FioSetupMixin,
    FioUtilsMixin,
    TestControlMixin,
    ProcessManagerMixin,
    BridgeStatusMixin,
    DiskBenchBridgeCore,
):
    """Bridge between web GUI and diskbench helper binary.

    Assembled from:
      - DiskBenchBridgeCore  (init, state, JSON extraction, simple commands)
      - BridgeStatusMixin    (background-test status, live metrics)
      - ProcessManagerMixin  (execute cmd, run-thread, FIO cleanup)
      - TestControlMixin     (start / stop / stop-all)
      - FioUtilsMixin        (direct FIO tests, QLab tests)
      - FioSetupMixin        (SHM detection, compilation, auto-fix)
    """
    pass


# --- Server entry-point -----------------------------------------------

def main():
    """Main server function."""
    print("QLab Disk Performance Tester Bridge Server starting...")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr,
    )
    logger = logging.getLogger(__name__)

    bridge = DiskBenchBridge()
    server_address = ('localhost', 8765)
    handler_class = create_request_handler(bridge)

    try:
        httpd = ThreadedHTTPServer(server_address, handler_class)
        logger.info("Starting QLab Disk Performance Tester Bridge Server")
        logger.info(f"Server running at http://{server_address[0]}:{server_address[1]}")
        logger.info(f"Web GUI at http://{server_address[0]}:{server_address[1]}/")
        logger.info("Press Ctrl+C to stop the server")
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        if 'httpd' in locals():
            httpd.shutdown()
            httpd.server_close()


if __name__ == '__main__':
    main()
