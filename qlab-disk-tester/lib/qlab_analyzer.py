import json

class QLabAnalyzer:
    def __init__(self):
        # ProRes 422 Streaming-Szenario @ 50fps
        # 1x 4K ProRes 422 + 3x HD ProRes 422 (normal + 3x für Überblendung)
        self.PRORES_422_4K_MBPS = 440  # MB/s für 4K @ 50fps
        self.PRORES_422_HD_MBPS = 72   # MB/s für HD @ 50fps
        
        # Berechnung der Datenraten
        self.NORMAL_BANDWIDTH = self.PRORES_422_4K_MBPS + (3 * self.PRORES_422_HD_MBPS)  # 656 MB/s
        self.CROSSFADE_BANDWIDTH = self.NORMAL_BANDWIDTH * 3  # 1968 MB/s
        self.SAFETY_BUFFER_BANDWIDTH = 2100  # MB/s mit Sicherheitspuffer
        
        # Legacy compatibility für mögliche Stream-Berechnung
        self.PRORES_HQ_4K_MBPS = 92  # Behalten für Rückwärtskompatibilität

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
                    # Process read metrics if read has actual data
                    if "read" in job:
                        read_bw_bytes = job["read"].get("bw_bytes", 0)
                        if read_bw_bytes > 0:  # Only use if there's actual read data
                            read_bw_mbps = max(read_bw_mbps, read_bw_bytes / (1024 * 1024))  # Convert bytes/s to MB/s
                            read_iops = max(read_iops, job["read"].get("iops", 0))
                            read_lat_avg_ms = max(read_lat_avg_ms, job["read"].get("lat_ns", {}).get("mean", 0) / 1_000_000)
                            read_lat_99th_ms = max(read_lat_99th_ms, job["read"].get("clat_ns", {}).get("percentile", {}).get("99.000000", 0) / 1_000_000)
                    
                    # Process write metrics if write has actual data
                    if "write" in job:
                        write_bw_bytes = job["write"].get("bw_bytes", 0)
                        if write_bw_bytes > 0:  # Only use if there's actual write data
                            write_bw_mbps = max(write_bw_mbps, write_bw_bytes / (1024 * 1024))  # Convert bytes/s to MB/s
                            write_iops = max(write_iops, job["write"].get("iops", 0))
                            write_lat_avg_ms = max(write_lat_avg_ms, job["write"].get("lat_ns", {}).get("mean", 0) / 1_000_000)
                            write_lat_99th_ms = max(write_lat_99th_ms, job["write"].get("clat_ns", {}).get("percentile", {}).get("99.000000", 0) / 1_000_000)
        
        # ProRes 422 Stream-Berechnung
        possible_prores422_streams = 0
        if read_bw_mbps > 0:
            # Berechnung basierend auf ProRes 422 HD (72 MB/s) für Stream-Anzahl
            possible_prores422_streams = int(read_bw_mbps / self.PRORES_422_HD_MBPS)
        
        # Legacy 4K Stream-Berechnung für Kompatibilität
        possible_4k_streams = 0
        if read_bw_mbps > 0:
            possible_4k_streams = int(read_bw_mbps / self.PRORES_HQ_4K_MBPS)

        stream_performance = "❌ POOR"
        cue_response_time = "❌ POOR"
        suitability_rating = "❌"
        recommendation = "Ungeeignet für ProRes 422 4K+HD Setup."

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

        # Criteria für ProRes 422 QLab-Suitability
        if read_bw_mbps >= self.SAFETY_BUFFER_BANDWIDTH:  # >= 2100 MB/s
            stream_performance = "✅ EXCELLENT"
            if read_lat_99th_ms < 10:  # 99th percentile latency < 10ms
                cue_response_time = "✅ EXCELLENT"
                suitability_rating = "✅"
                recommendation = f"Perfekt für ProRes 422 Setup mit {possible_prores422_streams} HD-Streams. Unterstützt Überblendungs-Peaks bis 2100 MB/s."
            elif read_lat_99th_ms < 20:
                cue_response_time = "⚠️ ACCEPTABLE"
                suitability_rating = "✅"
                recommendation = f"Sehr gut für ProRes 422 Setup ({possible_prores422_streams} HD-Streams), aber Latenz während Shows überwachen."
            else:
                cue_response_time = "❌ POOR"
                suitability_rating = "⚠️"
                recommendation = "Gute Bandwidth, aber hohe Latenz kann Cue-Response beeinträchtigen. Gründlich testen."
        elif read_bw_mbps >= self.NORMAL_BANDWIDTH:  # >= 656 MB/s
            stream_performance = "⚠️ ACCEPTABLE"
            suitability_rating = "⚠️"
            recommendation = f"Geeignet für Normal-Betrieb ({possible_prores422_streams} HD-Streams), aber Überblendungen können problematisch werden. Upgrade für volle Performance empfohlen."
        elif read_bw_mbps >= 400:
            stream_performance = "⚠️ LIMITED"
            suitability_rating = "⚠️"
            recommendation = f"Begrenzte ProRes 422 Unterstützung ({possible_prores422_streams} HD-Streams). Für kritische Shows Upgrade auf Thunderbolt/USB 3.2+ erforderlich."
        else:
            stream_performance = "❌ POOR"
            suitability_rating = "❌"
            recommendation = f"Ungeeignet für ProRes 422 4K+HD Setup. Aktuelle Verbindung ({connection_type}) zu langsam. Upgrade auf USB 3.0+ oder interne SSD erforderlich."

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
                "possible_4k_streams": possible_prores422_streams,
                "stream_performance": stream_performance,
                "cue_response_time": cue_response_time,
                "suitability_rating": suitability_rating,
                "recommendation": recommendation
            }
        }
        return analysis_results

if __name__ == "__main__":
    # Example Usage with dummy fio results
    dummy_fio_results = [
        {
            "jobs": [
                {
                    "jobname": "standard_qlab_read",
                    "read": {
                        "bw_bytes": 1000 * 1024 * 1024, # 1000 MB/s
                        "iops": 250,
                        "lat_ns": {"mean": 5_000_000}, # 5ms
                        "clat_ns": {"percentile": {"99.000000": 9_000_000}} # 9ms
                    },
                    "write": {
                        "bw_bytes": 0, "iops": 0, "lat_ns": {"mean": 0}, "clat_ns": {"percentile": {"99.000000": 0}}
                    }
                }
            ]
        },
        {
            "jobs": [
                {
                    "jobname": "quick_seq_write",
                    "read": {
                        "bw_bytes": 0, "iops": 0, "lat_ns": {"mean": 0}, "clat_ns": {"percentile": {"99.000000": 0}}
                    },
                    "write": {
                        "bw_bytes": 800 * 1024 * 1024, # 800 MB/s
                        "iops": 200,
                        "lat_ns": {"mean": 6_000_000}, # 6ms
                        "clat_ns": {"percentile": {"99.000000": 12_000_000}} # 12ms
                    }
                }
            ]
        }
    ]

    analyzer = QLabAnalyzer()
    analysis = analyzer.analyze_fio_results(dummy_fio_results)
    print(json.dumps(analysis, indent=2))

    # Example with poor performance
    poor_fio_results = [
        {
            "jobs": [
                {
                    "jobname": "standard_qlab_read",
                    "read": {
                        "bw_bytes": 300 * 1024 * 1024, # 300 MB/s
                        "iops": 50,
                        "lat_ns": {"mean": 50_000_000}, # 50ms
                        "clat_ns": {"percentile": {"99.000000": 100_000_000}} # 100ms
                    },
                    "write": {
                        "bw_bytes": 0, "iops": 0, "lat_ns": {"mean": 0}, "clat_ns": {"percentile": {"99.000000": 0}}
                    }
                }
            ]
        }
    ]
    poor_analysis = analyzer.analyze_fio_results(poor_fio_results)
    print("\n--- Poor Performance Example ---")
    print(json.dumps(poor_analysis, indent=2))
