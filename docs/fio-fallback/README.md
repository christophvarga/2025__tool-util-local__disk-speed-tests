# Direct FIO Usage (Fallback)

Version 1.0 – 5.9.2025

This folder provides ready-to-use FIO config templates and a short guide for running tests directly with fio, without the bridge server or diskbench CLI.

What you get
- Four FIO configs mirroring the built-in tests: quick_max_mix, prores_422_real, prores_422_hq_real, thermal_maximum.
- Placeholders ${TEST_FILE} and ${TEST_SIZE} – you replace them before running.
- Safe-by-default notes for macOS (FIO_DISABLE_SHM).
- Basic result interpretation and jq snippets to extract key metrics.

Prerequisites
- Install fio or place a vendored binary:
  - Homebrew: brew install fio
  - Vendored: vendor/fio/macos/<arch>/fio; mark executable: chmod +x vendor/fio/macos/<arch>/fio
- macOS tip: export FIO_DISABLE_SHM=1 to avoid shared memory issues with some builds.

Quick start
1) Choose a target volume and file path (mounted filesystem recommended for QLab realism):
   export TEST_FILE="/Volumes/TargetDisk/diskbench_fallback.dat"
   export TEST_SIZE="10G"   # 1–1000G
   export FIO_DISABLE_SHM=1  # recommended on macOS

2) Generate a concrete FIO config from a template and run:
   envsubst < quick_max_mix.fio > /tmp/quick_max_mix.fio
   fio --output-format=json --output=/tmp/quick_max_mix.json /tmp/quick_max_mix.fio

3) Inspect results (examples):
   # Per-job read/write bandwidth and iops (prefers modern fields, falls back if missing)
   jq \
     '{jobs: [.jobs[] | {name: .jobname, read_bw_kib: (.read.bw // ((.read.bw_bytes // 1024) // 1)), write_bw_kib: (.write.bw // ((.write.bw_bytes // 1024) // 1)), read_iops: (.read.iops // .read.iops_mean), write_iops: (.write.iops // .write.iops_mean)}]}' \
     /tmp/quick_max_mix.json

4) Cleanup the test file when done:
   rm -f "$TEST_FILE"

Templates
- quick_max_mix.fio: 5-minute mixed workload for quick analysis
- prores_422_real.fio: 30-minute real-world ProRes 422 pattern
- prores_422_hq_real.fio: 30-minute ProRes 422 HQ pattern (higher bandwidth)
- thermal_maximum.fio: 60-minute endurance pattern

Result interpretation (QLab-oriented, rough guide)
- Excellent: seq read >= 300 MB/s, latency < 2 ms, random read IOPS >= 50k
- Good: seq read >= 200 MB/s, latency < 5 ms, random read IOPS >= 20k
- Fair: basic usage; pre-load cues; avoid rapid sequences
- Poor: not suitable for live performance

Notes
- You can use different TEST_FILE per run to avoid filesystem cache effects.
- If your FIO shows only bw_bytes (not bw), convert bytes/s to KiB/s by dividing by 1024.
- For raw devices (/dev/diskN), admin privileges may be required and results differ from QLab reality; prefer mounted volumes.

