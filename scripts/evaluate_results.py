#!/usr/bin/env python3
"""
Evaluate diskbench or raw FIO JSON against QLab show targets.

Usage:
  python scripts/evaluate_results.py --input path/to/results.json [--test-type quick_max_mix|prores_422_real|prores_422_hq_real|thermal_maximum] [--output report.json]

Notes:
- Automatically detects diskbench JSON (top-level 'fio_results') vs raw FIO JSON (top-level 'jobs').
- Throughput comparisons use read bandwidth in MB/s (KiB/s / 1024) aggregated across jobs.
- Latency uses avg_read_latency from diskbench summary if available, else computes mean(ns)->ms across jobs.
- Stability for show tests is approximated via (sum bw_min / sum bw_mean) if fields exist; otherwise 'unknown'.

Thresholds (raised minima):
- quick_max_mix: min_bw_mb=300, rec_bw_mb=500, lat_ms<=2.0, iops_min=20000
- prores_422_real: min_bw_mb=350, rec_bw_mb=500, excellent>=600, lat_ms<=3.0
- prores_422_hq_real: min_bw_mb=700, rec_bw_mb=1000, excellent>=1200, lat_ms<=3.0
- thermal_maximum: min_bw_mb=400, stability_ratio_min=0.7, lat_ms<=3.0
"""
import argparse
import json
import sys
from typing import Dict, Any, Tuple

THRESHOLDS = {
    "quick_max_mix": {
        "min_bw_mb": 300,
        "rec_bw_mb": 500,
        "excellent_bw_mb": 600,
        "lat_ms": 2.0,
        "iops_min": 20000,
    },
    "prores_422_real": {
        "min_bw_mb": 350,
        "rec_bw_mb": 500,
        "excellent_bw_mb": 600,
        "lat_ms": 3.0,
    },
    "prores_422_hq_real": {
        "min_bw_mb": 700,
        "rec_bw_mb": 1000,
        "excellent_bw_mb": 1200,
        "lat_ms": 3.0,
    },
    "thermal_maximum": {
        "min_bw_mb": 400,
        "lat_ms": 3.0,
        "stability_ratio_min": 0.7,  # bw_min / bw_mean across jobs
    },
}


def _is_diskbench_payload(data: Dict[str, Any]) -> bool:
    return isinstance(data, dict) and "fio_results" in data and isinstance(data["fio_results"], dict)


def _extract_summary_from_diskbench(data: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    info = data.get("test_info", {})
    test_type = info.get("test_mode") or info.get("test_name") or "unknown"
    fio = data.get("fio_results", {})
    summary = fio.get("summary", {})
    jobs = fio.get("jobs", [])
    return {"summary": summary, "jobs": jobs}, str(test_type)


def _extract_summary_from_fio(data: Dict[str, Any]) -> Dict[str, Any]:
    jobs = data.get("jobs", [])
    # Aggregate like diskbench.core.fio_runner
    def _bw_kib(io: Dict[str, Any]) -> float:
        if not isinstance(io, dict):
            return 0.0
        bw = io.get("bw", 0) or 0
        if not bw:
            bw = (io.get("bw_bytes", 0) or 0) / 1024.0
        return float(bw)

    total_read_iops = 0.0
    total_write_iops = 0.0
    total_read_bw_kib = 0.0
    total_write_bw_kib = 0.0
    read_latencies_ns = []
    write_latencies_ns = []
    # Stability estimation
    sum_bw_min = 0.0
    sum_bw_mean = 0.0

    for job in jobs:
        read = job.get("read", {})
        write = job.get("write", {})
        total_read_iops += float(read.get("iops", read.get("iops_mean", 0.0)) or 0.0)
        total_write_iops += float(write.get("iops", write.get("iops_mean", 0.0)) or 0.0)
        total_read_bw_kib += _bw_kib(read)
        total_write_bw_kib += _bw_kib(write)
        rl = read.get("lat_ns", {}).get("mean", 0)
        wl = write.get("lat_ns", {}).get("mean", 0)
        if rl:
            read_latencies_ns.append(float(rl))
        if wl:
            write_latencies_ns.append(float(wl))
        # Stability fields if present
        if isinstance(read, dict):
            sum_bw_min += float(read.get("bw_min", 0.0) or 0.0)
            sum_bw_mean += float(read.get("bw_mean", _bw_kib(read)) or 0.0)

    avg_read_latency_ms = (sum(read_latencies_ns) / len(read_latencies_ns) / 1_000_000.0) if read_latencies_ns else 0.0
    avg_write_latency_ms = (sum(write_latencies_ns) / len(write_latencies_ns) / 1_000_000.0) if write_latencies_ns else 0.0

    summary = {
        "total_read_iops": total_read_iops,
        "total_write_iops": total_write_iops,
        "total_read_bw": total_read_bw_kib,   # KiB/s
        "total_write_bw": total_write_bw_kib, # KiB/s
        "avg_read_latency": avg_read_latency_ms,
        "avg_write_latency": avg_write_latency_ms,
        "stability_ratio": (sum_bw_min / sum_bw_mean) if sum_bw_mean > 0 else None,
    }
    return {"summary": summary, "jobs": jobs}


def _mbps_from_kib(kib: float) -> float:
    return float(kib) / 1024.0


def evaluate(test_type: str, summary: Dict[str, Any]) -> Dict[str, Any]:
    test_type = str(test_type)
    # Normalize legacy aliases
    aliases = {
        "quick_max_speed": "quick_max_mix",
        "qlab_prores_422_show": "prores_422_real",
        "qlab_prores_hq_show": "prores_422_hq_real",
        "max_sustained": "thermal_maximum",
    }
    if test_type in aliases:
        test_type = aliases[test_type]

    thr = THRESHOLDS.get(test_type)
    if not thr:
        # Default conservative thresholds
        thr = {"min_bw_mb": 300, "lat_ms": 3.0}

    read_bw_mb = _mbps_from_kib(summary.get("total_read_bw", 0.0) or 0.0)
    read_iops = float(summary.get("total_read_iops", 0.0) or 0.0)
    read_lat = float(summary.get("avg_read_latency", 0.0) or 0.0)
    stability_ratio = summary.get("stability_ratio")

    status = "fail"
    reasons = []

    # Base checks
    if read_bw_mb < thr.get("min_bw_mb", 0):
        reasons.append(f"read_bw_mb {read_bw_mb:.1f} < min {thr['min_bw_mb']}")
    if read_lat and read_lat > thr.get("lat_ms", 999):
        reasons.append(f"latency {read_lat:.2f}ms > {thr['lat_ms']}ms")
    if test_type == "quick_max_mix" and read_iops < thr.get("iops_min", 0):
        reasons.append(f"read_iops {read_iops:.0f} < min {thr['iops_min']}")
    if test_type in ("prores_422_real", "prores_422_hq_real", "thermal_maximum") and stability_ratio is not None:
        min_ratio = thr.get("stability_ratio_min", 0.0)
        if min_ratio and stability_ratio < min_ratio:
            reasons.append(f"stability_ratio {stability_ratio:.2f} < {min_ratio}")

    if not reasons:
        # Meets minimums; check for recommended/excellent
        rec = thr.get("rec_bw_mb")
        exc = thr.get("excellent_bw_mb") or (rec * 1.2 if rec else None)
        if exc and read_bw_mb >= exc and read_lat <= thr.get("lat_ms", 999):
            status = "excellent"
        elif rec and read_bw_mb >= rec and read_lat <= thr.get("lat_ms", 999):
            status = "pass"
        else:
            status = "pass"  # meets minimums
    else:
        status = "fail"

    return {
        "test_type": test_type,
        "metrics": {
            "read_bw_mb": round(read_bw_mb, 1),
            "read_iops": round(read_iops, 1),
            "avg_read_latency_ms": round(read_lat, 3),
            "stability_ratio": round(stability_ratio, 3) if isinstance(stability_ratio, (int, float)) else None,
        },
        "thresholds": thr,
        "status": status,
        "reasons": reasons,
    }


def main():
    ap = argparse.ArgumentParser(description="Evaluate diskbench/FIO results for QLab show readiness")
    ap.add_argument("--input", required=True, help="Path to diskbench or raw FIO JSON")
    ap.add_argument("--test-type", default=None, help="Override test type if not embedded in JSON")
    ap.add_argument("--output", default=None, help="Optional output file for evaluation JSON")
    args = ap.parse_args()

    with open(args.input, "r") as f:
        data = json.load(f)

    if _is_diskbench_payload(data):
        extracted, embedded_type = _extract_summary_from_diskbench(data)
        test_type = args.test_type or embedded_type
    elif isinstance(data, dict) and "jobs" in data:
        extracted = _extract_summary_from_fio(data)
        test_type = args.test_type or "unknown"
    else:
        print("Unrecognized JSON format: expected diskbench payload or FIO 'jobs'", file=sys.stderr)
        sys.exit(2)

    result = evaluate(test_type, extracted.get("summary", {}))

    out = json.dumps(result, indent=2)
    if args.output:
        with open(args.output, "w") as fo:
            fo.write(out)
    print(out)


if __name__ == "__main__":
    main()

