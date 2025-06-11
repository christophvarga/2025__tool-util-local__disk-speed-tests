import json
import os
from datetime import datetime

import os

class ReportGenerator:
    def __init__(self, colors):
        self.colors = colors
        # Get template path relative to current file location
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.template_path = os.path.join(current_dir, "..", "templates", "report_template.json")

    def generate_cli_report(self, analysis_results):
        """Generates a colorful CLI report from the analysis results."""
        if not analysis_results:
            print(f"{self.colors.FAIL}No analysis results to report.{self.colors.ENDC}")
            return

        metrics = analysis_results["performance_metrics"]
        suitability = analysis_results["qlab_suitability"]

        print(f"\n{self.colors.HEADER}╔══════════════════════════════════════════════════════════════╗{self.colors.ENDC}")
        print(f"{self.colors.HEADER}║                    QLab Disk Performance Tester              ║{self.colors.ENDC}")
        print(f"{self.colors.HEADER}║                  Professional Video Storage Testing          ║{self.colors.ENDC}")
        print(f"{self.colors.HEADER}╚══════════════════════════════════════════════════════════════╝{self.colors.ENDC}")

        print(f"\n{self.colors.OKCYAN}📊 PERFORMANCE METRICS{self.colors.ENDC}")
        print(f"  Bandwidth (Read): {self.colors.BOLD}{metrics['read_bandwidth_mbps']:.2f} MB/s{self.colors.ENDC}")
        print(f"  IOPS (Read):      {self.colors.BOLD}{metrics['read_iops']:.0f}{self.colors.ENDC}")
        print(f"  Latency (avg):    {self.colors.BOLD}{metrics['read_latency_ms_avg']:.2f} ms{self.colors.ENDC}")
        print(f"  Latency (99%):    {self.colors.BOLD}{metrics['read_latency_ms_99th']:.2f} ms{self.colors.ENDC}")
        
        if metrics['write_bandwidth_mbps'] > 0:
            print(f"\n{self.colors.OKCYAN}📝 WRITE METRICS (if applicable){self.colors.ENDC}")
            print(f"  Bandwidth (Write): {self.colors.BOLD}{metrics['write_bandwidth_mbps']:.2f} MB/s{self.colors.ENDC}")
            print(f"  IOPS (Write):      {self.colors.BOLD}{metrics['write_iops']:.0f}{self.colors.ENDC}")
            print(f"  Latency (avg):     {self.colors.BOLD}{metrics['write_latency_ms_avg']:.2f} ms{self.colors.ENDC}")
            print(f"  Latency (99%):     {self.colors.BOLD}{metrics['write_latency_ms_99th']:.2f} ms{self.colors.ENDC}")


        print(f"\n{self.colors.OKCYAN}🎬 QLAB SUITABILITY ANALYSIS{self.colors.ENDC}")
        print(f"  4K ProRes HQ Streams: {self.colors.BOLD}{suitability['possible_4k_streams']} simultaneous{self.colors.ENDC}")
        print(f"  Stream Performance:   {self._get_colored_status(suitability['stream_performance'])}")
        print(f"  Cue Response Time:    {self._get_colored_status(suitability['cue_response_time'])}")

        print(f"\n{self.colors.OKCYAN}💡 RECOMMENDATIONS{self.colors.ENDC}")
        print(f"  {self._get_colored_status(suitability['suitability_rating'])} {suitability['recommendation']}")
        print("\n")

    def _get_colored_status(self, status):
        """Helper to colorize status strings."""
        if "EXCELLENT" in status or "✅" in status:
            return f"{self.colors.OKGREEN}{self.colors.BOLD}{status}{self.colors.ENDC}"
        elif "ACCEPTABLE" in status or "⚠️" in status:
            return f"{self.colors.WARNING}{self.colors.BOLD}{status}{self.colors.ENDC}"
        elif "POOR" in status or "❌" in status:
            return f"{self.colors.FAIL}{self.colors.BOLD}{status}{self.colors.ENDC}"
        return status # Default

    def export_json_results(self, analysis_results, raw_fio_results, selected_ssd, selected_mode, output_dir="results"):
        """Exports detailed results to a JSON file."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ssd_name_clean = selected_ssd['Name'].replace(" ", "_").replace("/", "_")
        mode_name_clean = selected_mode['mode'].replace(" ", "_")
        filename = f"qlab_test_report_{ssd_name_clean}_{mode_name_clean}_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)

        full_report = {
            "timestamp": datetime.now().isoformat(),
            "selected_ssd": selected_ssd,
            "selected_test_mode": selected_mode,
            "analysis_results": analysis_results,
            "raw_fio_results": raw_fio_results
        }

        try:
            with open(filepath, 'w') as f:
                json.dump(full_report, f, indent=4)
            print(f"{self.colors.OKGREEN}Detailed JSON report saved to: {filepath}{self.colors.ENDC}")
        except Exception as e:
            print(f"{self.colors.FAIL}Error saving JSON report: {e}{self.colors.ENDC}")

if __name__ == "__main__":
    # Dummy Colors class for standalone testing
    class DummyColors:
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKCYAN = '\033[96m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'

    # Example Usage with dummy analysis results
    dummy_analysis_results = {
        "performance_metrics": {
            "read_bandwidth_mbps": 789.2,
            "read_iops": 197,
            "read_latency_ms_avg": 4.85,
            "read_latency_ms_99th": 8.98,
            "write_bandwidth_mbps": 500.0,
            "write_iops": 150,
            "write_latency_ms_avg": 6.00,
            "write_latency_ms_99th": 10.50
        },
        "qlab_suitability": {
            "possible_4k_streams": 8,
            "stream_performance": "✅ EXCELLENT",
            "cue_response_time": "✅ EXCELLENT",
            "suitability_rating": "✅",
            "recommendation": "Perfect for professional 4K QLab production"
        }
    }

    dummy_raw_fio_results = [{"fio_version": "fio-3.28", "jobs": []}] # Simplified
    dummy_selected_ssd = {"Name": "MySSD", "Mount Point": "/Volumes/MySSD"}
    dummy_selected_mode = {"name": "Standard QLab Test", "mode": "standard_qlab"}

    reporter = ReportGenerator(DummyColors())
    reporter.generate_cli_report(dummy_analysis_results)
    reporter.export_json_results(dummy_analysis_results, dummy_raw_fio_results, dummy_selected_ssd, dummy_selected_mode)

    # Example with warning
    dummy_analysis_warning = {
        "performance_metrics": {
            "read_bandwidth_mbps": 500.0,
            "read_iops": 120,
            "read_latency_ms_avg": 15.0,
            "read_latency_ms_99th": 25.0,
            "write_bandwidth_mbps": 0, "write_iops": 0, "write_latency_ms_avg": 0, "write_latency_ms_99th": 0
        },
        "qlab_suitability": {
            "possible_4k_streams": 5,
            "stream_performance": "⚠️ ACCEPTABLE",
            "cue_response_time": "⚠️ ACCEPTABLE",
            "suitability_rating": "⚠️",
            "recommendation": "May be suitable for lighter 4K QLab production (fewer streams). Test thoroughly."
        }
    }
    print("\n--- Warning Example ---")
    reporter.generate_cli_report(dummy_analysis_warning)
