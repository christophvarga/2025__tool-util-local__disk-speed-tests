import json

class QLabAnalyzer:
    def __init__(self):
        # Approximate 4K ProRes HQ data rate for 24fps (92 MB/s)
        # Using a conservative estimate for calculation
        self.PRORES_HQ_4K_MBPS = 92 # MB/s per stream
        # Enhanced QLab requirements for professional use
        self.QLAB_TARGET_STREAMS = 8  # 4 files with frame blending = 8 streams
        self.QLAB_MIN_BANDWIDTH = self.QLAB_TARGET_STREAMS * self.PRORES_HQ_4K_MBPS  # 736 MB/s minimum

    def analyze_fio_results(self, fio_results):
        """
        Analyzes raw fio JSON results to extract key metrics and QLab suitability.
        fio_results is expected to be a list of JSON objects, one for each job.
        """
        if not fio_results:
            return None

        # Initialize aggregated metrics
        aggregated_metrics = {
            "read_bandwidth_mbps": 0,
            "read_iops": 0,
            "read_latency_ms_avg": 0,
            "read_latency_ms_99th": 0,
            "write_bandwidth_mbps": 0,
            "write_iops": 0,
            "write_latency_ms_avg": 0,
            "write_latency_ms_99th": 0,
            "jobs_count": 0
        }

        # Aggregate results from all jobs
        for result in fio_results:
            if "jobs" in result:
                for job in result["jobs"]:
                    aggregated_metrics["jobs_count"] += 1
                    if "read" in job:
                        aggregated_metrics["read_bandwidth_mbps"] += job["read"].get("bw_bytes", 0) / (1024 * 1024)
                        aggregated_metrics["read_iops"] += job["read"].get("iops", 0)
                        aggregated_metrics["read_latency_ms_avg"] += job["read"].get("lat_ns", {}).get("mean", 0) / 1_000_000
                        aggregated_metrics["read_latency_ms_99th"] += job["read"].get("clat_ns", {}).get("percentile", {}).get("99.000000", 0) / 1_000_000
                    if "write" in job:
                        aggregated_metrics["write_bandwidth_mbps"] += job["write"].get("bw_bytes", 0) / (1024 * 1024)
                        aggregated_metrics["write_iops"] += job["write"].get("iops", 0)
                        aggregated_metrics["write_latency_ms_avg"] += job["write"].get("lat_ns", {}).get("mean", 0) / 1_000_000
                        aggregated_metrics["write_latency_ms_99th"] += job["write"].get("clat_ns", {}).get("percentile", {}).get("99.000000", 0) / 1_000_000
        
        # Average aggregated metrics if multiple jobs
        if aggregated_metrics["jobs_count"] > 0:
            # For simplicity, we'll average across jobs. Fio's group_reporting already aggregates.
            # If multiple jobs are run sequentially, we might want to report each job's metrics
            # or sum them if they represent parallel operations.
            # For now, we'll assume the primary job's metrics are representative or sum them if they are parallel.
            # Fio's group_reporting should give us the aggregate for parallel jobs.
            # Let's just take the first job's group_reporting if available, or sum if not.
            # For now, let's assume the fio_results list contains one aggregated result per test type (read/write/randread)
            # and we want to report the most relevant one.
            pass # The current fio_engine returns a list of results, one per job.
                 # We need to decide how to combine them for the final report.
                 # For now, let's focus on the read performance for QLab suitability.
        
        # Let's refine this: fio_engine returns a list of results, each result is a JSON output from one fio run.
        # Each fio run can have multiple jobs if --numjobs is used.
        # We need to extract the relevant metrics from the 'jobs' array within each result.
        
        # Re-initialize for a more specific extraction
        read_bw_mbps = 0
        read_iops = 0
        read_lat_avg_ms = 0
        read_lat_99th_ms = 0
        write_bw_mbps = 0
        write_iops = 0
        write_lat_avg_ms = 0
        write_lat_99th_ms = 0
        
        # Iterate through all fio results and jobs
        for result in fio_results:
            if "jobs" in result:
                for job in result["jobs"]:
                    # Only process read jobs for read metrics
                    if "read" in job and "write" not in job:
                        # Use 'bw_bytes' (bytes/s) for accurate bandwidth calculation
                        read_bw_bytes = job["read"].get("bw_bytes", 0)
                        read_bw_mbps = read_bw_bytes / (1024 * 1024)  # Convert bytes/s to MB/s
                        read_iops = job["read"].get("iops", 0)
                        read_lat_avg_ms = job["read"].get("lat_ns", {}).get("mean", 0) / 1_000_000
                        read_lat_99th_ms = job["read"].get("clat_ns", {}).get("percentile", {}).get("99.000000", 0) / 1_000_000
                    
                    # Only process write jobs for write metrics
                    if "write" in job and "read" not in job:
                        write_bw_bytes = job["write"].get("bw_bytes", 0)
                        write_bw_mbps = write_bw_bytes / (1024 * 1024)  # Convert bytes/s to MB/s
                        write_iops = job["write"].get("iops", 0)
                        write_lat_avg_ms = job["write"].get("lat_ns", {}).get("mean", 0) / 1_000_000
                        write_lat_99th_ms = job["write"].get("clat_ns", {}).get("percentile", {}).get("99.000000", 0) / 1_000_000
        
        # QLab Suitability Analysis
        possible_4k_streams = 0
        if read_bw_mbps > 0:
            possible_4k_streams = int(read_bw_mbps / self.PRORES_HQ_4K_MBPS)

        stream_performance = "❌ POOR"
        cue_response_time = "❌ POOR"
        suitability_rating = "❌"
        recommendation = "Not suitable for professional 4K QLab production."

        # Enhanced QLab suitability analysis with connection type awareness
        # Detect likely connection type based on performance
        connection_type = "Unknown"
        if read_bw_mbps > 2000:
            connection_type = "Internal NVMe (PCIe)"
        elif read_bw_mbps > 800:
            connection_type = "Thunderbolt 3/4 or USB 3.2"
        elif read_bw_mbps > 400:
            connection_type = "USB 3.1 or Thunderbolt 2"
        elif read_bw_mbps > 100:
            connection_type = "USB 3.0"
        elif read_bw_mbps > 25:
            connection_type = "USB 2.0 (Limited)"
        else:
            connection_type = "USB 2.0 or slower"

        # Criteria for QLab suitability with realistic thresholds
        if possible_4k_streams >= 8:
            stream_performance = "✅ EXCELLENT"
            if read_lat_99th_ms < 10: # 99th percentile latency < 10ms
                cue_response_time = "✅ EXCELLENT"
                suitability_rating = "✅"
                recommendation = "Perfect for professional 4K QLab production with 8+ concurrent streams."
            elif read_lat_99th_ms < 20:
                cue_response_time = "⚠️ ACCEPTABLE"
                suitability_rating = "⚠️"
                recommendation = "Good for professional 4K QLab production, but monitor latency during shows."
            else:
                cue_response_time = "❌ POOR"
                suitability_rating = "⚠️"
                recommendation = "Good bandwidth, but high latency may affect cue response. Test thoroughly."
        elif possible_4k_streams >= 4:
            stream_performance = "⚠️ ACCEPTABLE"
            suitability_rating = "⚠️"
            recommendation = f"Suitable for lighter 4K QLab production (4-{possible_4k_streams} streams). Consider upgrading connection for full 8-stream capability."
        elif possible_4k_streams >= 2:
            stream_performance = "⚠️ LIMITED"
            suitability_rating = "⚠️"
            recommendation = f"Limited to {possible_4k_streams} 4K streams. Consider USB 3.0+ or Thunderbolt connection for QLab production."
        else:
            stream_performance = "❌ POOR"
            suitability_rating = "❌"
            recommendation = f"Insufficient bandwidth for 4K QLab production. Current connection ({connection_type}) limits performance. Upgrade to USB 3.0+ or internal drive."

        analysis_results = {
            "performance_metrics": {
                "read_bandwidth_mbps": round(read_bw_mbps, 2),
                "read_iops": round(read_iops, 2),
                "read_latency_ms_avg": round(read_lat_avg_ms, 2),
                "read_latency_ms_99th": round(read_lat_99th_ms, 2),
                "write_bandwidth_mbps": round(write_bw_mbps, 2),
                "write_iops": round(write_iops, 2),
                "write_latency_ms_avg": round(write_lat_avg_ms, 2),
                "write_latency_ms_99th": round(write_lat_99th_ms, 2)
            },
            "qlab_suitability": {
                "possible_4k_streams": possible_4k_streams,
                "stream_performance": stream_performance,
                "cue_response_time": cue_response_time,
                "suitability_rating": suitability_rating,
                "recommendation": recommendation
            }
        }
        return analysis_results
