#!/bin/bash
# FIO wrapper for macOS to avoid shared memory issues
export FIO_DISABLE_SHM=1
export TMPDIR=/tmp
export SHM_PATH=/tmp
exec "/Users/christophvarga/Documents/2000_software_lokal/2025_06_disk-speed-tests/fio-3.37/fio" "$@"
