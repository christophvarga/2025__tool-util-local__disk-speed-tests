# Evaluation Criteria – QLab Show Targets

Version 1.0 – 8.9.2025

Purpose
- Define pass/fail thresholds and recommendations for fio/diskbench results in the context of multi‑hour QLab show operation.
- Complements scripts/evaluate_results.py which implements these thresholds.

Terminology
- read_bw_mb: Aggregated read bandwidth across jobs in MB/s (KiB/s / 1024)
- avg_read_latency_ms: Average read latency in milliseconds
- stability_ratio: Sum(read.bw_min) / Sum(read.bw_mean) across jobs (if available)

Thresholds
- quick_max_mix (5 min, mixed workload)
  - Minimum: read_bw_mb ≥ 300, avg_read_latency_ms ≤ 2.0, read_iops ≥ 20,000
  - Recommended: read_bw_mb ≥ 500
  - Excellent: read_bw_mb ≥ 600

- prores_422_real (30 min, show-like pattern)
  - Minimum: read_bw_mb ≥ 350, avg_read_latency_ms ≤ 3.0
  - Recommended: read_bw_mb ≥ 500, stability_ratio ≥ 0.80
  - Excellent: read_bw_mb ≥ 600, stability_ratio ≥ 0.85

- prores_422_hq_real (30 min, higher bandwidth)
  - Minimum: read_bw_mb ≥ 700, avg_read_latency_ms ≤ 3.0
  - Recommended: read_bw_mb ≥ 1000, stability_ratio ≥ 0.80
  - Excellent: read_bw_mb ≥ 1200, stability_ratio ≥ 0.85

- thermal_maximum (60 min, endurance)
  - Minimum: read_bw_mb ≥ 400, avg_read_latency_ms ≤ 3.0
  - Recommended: stability_ratio ≥ 0.70, no sustained throughput drop > 20% over runtime
  - Excellent: stability_ratio ≥ 0.85, minimal drift in latency and throughput

Usage
- Diskbench JSON: python scripts/evaluate_results.py --input /path/to/diskbench.json
- Raw fio JSON: python scripts/evaluate_results.py --input /path/to/fio.json --test-type prores_422_real

Notes
- Prefer mounted volumes over raw devices for QLab realism.
- For raw devices (/dev/diskN), admin privileges may be required; results differ from actual QLab access patterns.

