import os
import time
import threading
import random
import json
from typing import Dict, Any, Optional, Callable

class PythonDiskEngine:
    """
    A pure Python disk performance testing engine as a fallback when fio is not available.
    This provides basic disk testing functionality without external dependencies.
    """
    
    def __init__(self, test_file_path="python_test_file"):
        self.test_file_path = test_file_path
        self.stop_flag = threading.Event()
    
    def execute_disk_test(self, test_mode: str, disk_path: str, test_size_gb: int, monitor=None) -> Optional[Dict[str, Any]]:
        """
        Execute disk performance tests using pure Python I/O operations.
        """
        # Reset stop flag for new test
        self.stop_flag.clear()
        
        try:
            if test_mode == "setup_check":
                return self._run_setup_check(disk_path, test_size_gb, monitor)
            elif test_mode == "qlab_pattern":
                return self._run_qlab_prores_422_pattern(disk_path, test_size_gb, monitor)
            elif test_mode == "qlab_hq_pattern":
                return self._run_qlab_prores_hq_pattern(disk_path, test_size_gb, monitor)
            elif test_mode == "baseline_streaming":
                return self._run_baseline_streaming(disk_path, test_size_gb, monitor)
            else:
                raise ValueError(f"Unknown test mode: {test_mode}")
        except Exception as e:
            if monitor:
                monitor.log_error(f"Python disk test failed: {e}")
            return None
    
    def _run_setup_check(self, disk_path: str, test_size_gb: int, monitor=None) -> Dict[str, Any]:
        """Run a basic setup check with read and write tests."""
        results = {
            "test_mode": "setup_check",
            "jobs": []
        }
        
        # Write test
        write_result = self._run_write_test(disk_path, min(test_size_gb, 1), 5, monitor, "setup_write")
        if write_result:
            results["jobs"].append(write_result)
        
        # Read test
        read_result = self._run_read_test(disk_path, min(test_size_gb, 1), 5, monitor, "setup_read")
        if read_result:
            results["jobs"].append(read_result)
        
        return results
    
    def _run_qlab_prores_422_pattern(self, disk_path: str, test_size_gb: int, monitor=None) -> Dict[str, Any]:
        """Run a QLab ProRes 422 pattern test (2.5 hours, 656→2100 MB/s)."""
        results = {
            "test_mode": "qlab_prores_422",
            "jobs": []
        }
        
        # Phase 1: Normal load (30 minutes)
        phase1_result = self._run_qlab_phase(
            disk_path, test_size_gb, 1800, monitor, 
            "prores_422_normal", target_mbps=656, crossfade_mbps=2100
        )
        if phase1_result:
            results["jobs"].append(phase1_result)
        
        # Phase 2: Show simulation with crossfades (1.5 hours)
        if not self.stop_flag.is_set():
            phase2_result = self._run_qlab_phase(
                disk_path, test_size_gb, 5400, monitor,
                "prores_422_show", target_mbps=656, crossfade_mbps=2100, crossfade_frequency=180
            )
            if phase2_result:
                results["jobs"].append(phase2_result)
        
        # Phase 3: Thermal recovery (30 minutes)
        if not self.stop_flag.is_set():
            phase3_result = self._run_qlab_phase(
                disk_path, test_size_gb, 1800, monitor,
                "prores_422_recovery", target_mbps=656, crossfade_mbps=2100
            )
            if phase3_result:
                results["jobs"].append(phase3_result)
        
        # Phase 4: Max Speed Test (5 minutes)
        if not self.stop_flag.is_set():
            max_speed_result = self._run_sustained_read_test(
                disk_path, test_size_gb, 300, monitor, "prores_422_max_speed"
            )
            if max_speed_result:
                results["jobs"].append(max_speed_result)
        
        return results
    
    def _run_qlab_prores_hq_pattern(self, disk_path: str, test_size_gb: int, monitor=None) -> Dict[str, Any]:
        """Run a QLab ProRes HQ 422 pattern test (2.5 hours, 950→3200 MB/s)."""
        results = {
            "test_mode": "qlab_prores_hq",
            "jobs": []
        }
        
        # Phase 1: Normal load (30 minutes)
        phase1_result = self._run_qlab_phase(
            disk_path, test_size_gb, 1800, monitor,
            "prores_hq_normal", target_mbps=950, crossfade_mbps=3200
        )
        if phase1_result:
            results["jobs"].append(phase1_result)
        
        # Phase 2: Show simulation with crossfades (1.5 hours)
        if not self.stop_flag.is_set():
            phase2_result = self._run_qlab_phase(
                disk_path, test_size_gb, 5400, monitor,
                "prores_hq_show", target_mbps=950, crossfade_mbps=3200, crossfade_frequency=180
            )
            if phase2_result:
                results["jobs"].append(phase2_result)
        
        # Phase 3: Thermal recovery (30 minutes)
        if not self.stop_flag.is_set():
            phase3_result = self._run_qlab_phase(
                disk_path, test_size_gb, 1800, monitor,
                "prores_hq_recovery", target_mbps=950, crossfade_mbps=3200
            )
            if phase3_result:
                results["jobs"].append(phase3_result)
        
        # Phase 4: Max Speed Test (5 minutes)
        if not self.stop_flag.is_set():
            max_speed_result = self._run_sustained_read_test(
                disk_path, test_size_gb, 300, monitor, "prores_hq_max_speed"
            )
            if max_speed_result:
                results["jobs"].append(max_speed_result)
        
        return results
    
    def _run_baseline_streaming(self, disk_path: str, test_size_gb: int, monitor=None) -> Dict[str, Any]:
        """Run a baseline streaming test (2 hours max sustained)."""
        results = {
            "test_mode": "baseline_streaming",
            "jobs": []
        }
        
        # 2-hour sustained max throughput test using optimized method
        read_result = self._run_sustained_read_test(disk_path, test_size_gb, 7200, monitor, "baseline_streaming")  # 2 hours
        if read_result:
            results["jobs"].append(read_result)
        
        return results
    
    def _run_qlab_phase(self, disk_path: str, test_size_gb: int, duration_sec: int, monitor=None, 
                       job_name="qlab_phase", target_mbps=656, crossfade_mbps=2100, crossfade_frequency=None) -> Optional[Dict[str, Any]]:
        """
        Run a QLab-specific test phase with realistic I/O patterns.
        
        Args:
            duration_sec: Phase duration in seconds
            target_mbps: Normal streaming throughput (MB/s)
            crossfade_mbps: Peak crossfade throughput (MB/s)
            crossfade_frequency: Seconds between crossfades (None = no crossfades)
        """
        if monitor:
            monitor.set_test_phase(f"QLab: {job_name}", duration_sec)
        
        # Create multiple test files to simulate video streams
        file_paths = []
        video_block_size = 1024 * 1024  # 1MB blocks for video streams
        mask_block_size = 4096  # 4KB blocks for masks/effects
        test_file_size = min(test_size_gb * 1024 * 1024 * 1024, 500 * 1024 * 1024)  # Max 500MB per file
        
        try:
            # Create 4 test files (1x 4K + 3x HD streams)
            for i in range(4):
                file_path = os.path.join(disk_path, f"{self.test_file_path}_{job_name}_stream_{i}")
                file_paths.append(file_path)
                
                # Create test file with video-like data
                with open(file_path, 'wb') as f:
                    for _ in range(test_file_size // video_block_size):
                        f.write(os.urandom(video_block_size))
            
            # Run the QLab simulation
            total_read_bytes = 0
            total_write_bytes = 0
            start_time = time.time()
            last_crossfade = start_time
            
            # Open all stream files
            stream_files = [open(fp, 'rb') for fp in file_paths]
            
            try:
                while time.time() - start_time < duration_sec and not self.stop_flag.is_set():
                    elapsed = time.time() - start_time
                    progress = min(100, (elapsed / duration_sec) * 100)
                    
                    # Determine if we're in a crossfade
                    in_crossfade = False
                    if crossfade_frequency and (elapsed - (last_crossfade - start_time)) >= crossfade_frequency:
                        in_crossfade = True
                        last_crossfade = time.time()
                    
                    # Calculate target throughput for this moment
                    current_target = crossfade_mbps if in_crossfade else target_mbps
                    
                    # Simulate video stream reads (95% of I/O)
                    for _ in range(int(current_target * 0.95 / len(stream_files))):  # Distribute across streams
                        for stream_file in stream_files:
                            if self.stop_flag.is_set():
                                break
                            
                            # Read video block
                            data = stream_file.read(video_block_size)
                            if not data:  # End of file, seek back
                                stream_file.seek(0)
                                data = stream_file.read(video_block_size)
                            
                            total_read_bytes += len(data)
                    
                    # Simulate random access for masks/effects (5% of I/O)
                    for _ in range(max(1, int(current_target * 0.05))):
                        if self.stop_flag.is_set():
                            break
                        
                        # Random small reads
                        random_file = random.choice(stream_files)
                        random_file.seek(random.randint(0, max(0, test_file_size - mask_block_size)))
                        data = random_file.read(mask_block_size)
                        total_read_bytes += len(data)
                    
                    # Calculate current throughput
                    current_mbps = (total_read_bytes / (1024 * 1024)) / elapsed if elapsed > 0 else 0
                    current_iops = int(total_read_bytes / video_block_size / elapsed) if elapsed > 0 else 0
                    
                    # Update monitor with current performance
                    if monitor:
                        phase_info = "🔥 CROSSFADE" if in_crossfade else "📹 NORMAL"
                        time_remaining = duration_sec - elapsed
                        hours = int(time_remaining // 3600)
                        minutes = int((time_remaining % 3600) // 60)
                        seconds = int(time_remaining % 60)
                        eta_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        
                        status = f"Phase: {job_name} | {phase_info} | Progress: {progress:.1f}% | Read: {current_mbps:.1f} MB/s | Target: {current_target:.0f} MB/s | ETA: {eta_str}"
                        monitor.update_with_fio_data(status)
                        
                        # Update GUI performance display
                        if hasattr(monitor, 'parent_window'):
                            monitor.parent_window.current_throughput = current_mbps
                            monitor.parent_window.current_iops = current_iops
                    
                    # Small delay to prevent overwhelming the system
                    time.sleep(0.1)
                
            finally:
                # Close all stream files
                for stream_file in stream_files:
                    stream_file.close()
            
            elapsed_time = time.time() - start_time
            avg_throughput_mbps = (total_read_bytes / (1024 * 1024)) / elapsed_time if elapsed_time > 0 else 0
            avg_iops = int(total_read_bytes / video_block_size / elapsed_time) if elapsed_time > 0 else 0
            
            return {
                "jobname": job_name,
                "read": {
                    "bw_bytes": int(total_read_bytes / elapsed_time) if elapsed_time > 0 else 0,
                    "bw": avg_throughput_mbps,
                    "iops": avg_iops,
                    "runtime_msec": int(elapsed_time * 1000)
                },
                "qlab_metrics": {
                    "target_mbps": target_mbps,
                    "crossfade_mbps": crossfade_mbps,
                    "phase_duration_sec": elapsed_time,
                    "crossfade_frequency_sec": crossfade_frequency
                }
            }
        
        except Exception as e:
            if monitor:
                monitor.log_error(f"QLab phase test failed: {e}")
            return None
        finally:
            # Clean up test files
            for file_path in file_paths:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except:
                    pass
    
    def _run_write_test(self, disk_path: str, size_gb: int, duration_sec: int, monitor=None, job_name="write_test") -> Optional[Dict[str, Any]]:
        """Run a sequential write test."""
        if monitor:
            monitor.set_test_phase(f"Python: {job_name}", duration_sec)
        
        file_path = os.path.join(disk_path, f"{self.test_file_path}_{job_name}")
        block_size = 64 * 1024  # 64KB blocks for better throughput
        total_bytes = 0
        start_time = time.time()
        
        try:
            with open(file_path, 'wb') as f:
                while time.time() - start_time < duration_sec and not self.stop_flag.is_set():
                    # Write 4KB of random data
                    data = os.urandom(block_size)
                    f.write(data)
                    f.flush()  # Ensure data is written to disk
                    os.fsync(f.fileno())  # Force sync to disk
                    total_bytes += block_size
                    
                    # Update progress
                    elapsed = time.time() - start_time
                    progress = min(100, (elapsed / duration_sec) * 100)
                    throughput_mbps = (total_bytes / (1024 * 1024)) / elapsed if elapsed > 0 else 0
                    
                    if monitor:
                        monitor.update_with_fio_data(f"Progress: {progress:.1f}% | Write: {throughput_mbps:.1f} MB/s")
                    
                    # Remove delay for better throughput measurement
                    # time.sleep(0.01)
            
            elapsed_time = time.time() - start_time
            throughput_mbps = (total_bytes / (1024 * 1024)) / elapsed_time if elapsed_time > 0 else 0
            
            return {
                "jobname": job_name,
                "write": {
                    "bw_bytes": int(total_bytes / elapsed_time) if elapsed_time > 0 else 0,
                    "bw": throughput_mbps,
                    "iops": int((total_bytes / block_size) / elapsed_time) if elapsed_time > 0 else 0,
                    "runtime_msec": int(elapsed_time * 1000)
                }
            }
        
        except Exception as e:
            if monitor:
                monitor.log_error(f"Write test failed: {e}")
            return None
        finally:
            # Clean up test file
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
    
    def _run_read_test(self, disk_path: str, size_gb: int, duration_sec: int, monitor=None, job_name="read_test") -> Optional[Dict[str, Any]]:
        """Run a sequential read test."""
        if monitor:
            monitor.set_test_phase(f"Python: {job_name}", duration_sec)
        
        # First create a test file to read from
        file_path = os.path.join(disk_path, f"{self.test_file_path}_{job_name}")
        block_size = 4096  # 4KB blocks
        test_file_size = min(size_gb * 1024 * 1024 * 1024, 100 * 1024 * 1024)  # Max 100MB for quick test
        
        try:
            # Create test file
            with open(file_path, 'wb') as f:
                for _ in range(test_file_size // block_size):
                    f.write(os.urandom(block_size))
            
            # Now read from it
            total_bytes = 0
            start_time = time.time()
            
            with open(file_path, 'rb') as f:
                while time.time() - start_time < duration_sec and not self.stop_flag.is_set():
                    # Read 4KB blocks
                    data = f.read(block_size)
                    if not data:  # End of file, seek back to beginning
                        f.seek(0)
                        continue
                    
                    total_bytes += len(data)
                    
                    # Update progress
                    elapsed = time.time() - start_time
                    progress = min(100, (elapsed / duration_sec) * 100)
                    throughput_mbps = (total_bytes / (1024 * 1024)) / elapsed if elapsed > 0 else 0
                    
                    if monitor:
                        monitor.update_with_fio_data(f"Progress: {progress:.1f}% | Read: {throughput_mbps:.1f} MB/s")
                    
                    # Remove delay for better throughput measurement
                    # time.sleep(0.01)
            
            elapsed_time = time.time() - start_time
            throughput_mbps = (total_bytes / (1024 * 1024)) / elapsed_time if elapsed_time > 0 else 0
            
            return {
                "jobname": job_name,
                "read": {
                    "bw_bytes": int(total_bytes / elapsed_time) if elapsed_time > 0 else 0,
                    "bw": throughput_mbps,
                    "iops": int((total_bytes / block_size) / elapsed_time) if elapsed_time > 0 else 0,
                    "runtime_msec": int(elapsed_time * 1000)
                }
            }
        
        except Exception as e:
            if monitor:
                monitor.log_error(f"Read test failed: {e}")
            return None
        finally:
            # Clean up test file
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
    
    def _run_sustained_read_test(self, disk_path: str, size_gb: int, duration_sec: int, monitor=None, job_name="sustained_read") -> Optional[Dict[str, Any]]:
        """Run a sustained read test optimized for maximum throughput measurement."""
        if monitor:
            monitor.set_test_phase(f"Python: {job_name} (Max Sustained)", duration_sec)
        
        # Create multiple large test files for sustained reading
        file_paths = []
        block_size = 1024 * 1024  # 1MB blocks for maximum throughput
        # Use larger files for sustained testing - up to 2GB per file
        test_file_size = min(size_gb * 1024 * 1024 * 1024, 2 * 1024 * 1024 * 1024)  # Max 2GB per file
        num_files = 4  # Multiple files to simulate real-world sustained load
        
        try:
            # Create multiple test files
            for i in range(num_files):
                file_path = os.path.join(disk_path, f"{self.test_file_path}_{job_name}_{i}")
                file_paths.append(file_path)
                
                if monitor:
                    monitor.update_with_fio_data(f"Creating test file {i+1}/{num_files}...")
                
                # Create test file with large blocks for better performance
                with open(file_path, 'wb') as f:
                    for block_num in range(test_file_size // block_size):
                        if self.stop_flag.is_set():
                            break
                        f.write(os.urandom(block_size))
                        
                        # Update creation progress
                        if block_num % 100 == 0:  # Update every 100MB
                            creation_progress = (block_num * block_size) / test_file_size * 100
                            if monitor:
                                monitor.update_with_fio_data(f"Creating file {i+1}/{num_files}: {creation_progress:.1f}%")
            
            if self.stop_flag.is_set():
                return None
            
            # Now perform sustained reading from all files
            total_bytes = 0
            start_time = time.time()
            
            # Open all files for reading
            file_handles = [open(fp, 'rb') for fp in file_paths]
            
            try:
                file_index = 0
                while time.time() - start_time < duration_sec and not self.stop_flag.is_set():
                    # Round-robin through files for sustained load
                    current_file = file_handles[file_index % len(file_handles)]
                    
                    # Read large blocks for maximum throughput
                    data = current_file.read(block_size)
                    if not data:  # End of file, seek back to beginning
                        current_file.seek(0)
                        data = current_file.read(block_size)
                    
                    total_bytes += len(data)
                    file_index += 1
                    
                    # Update progress every 10MB
                    if total_bytes % (10 * 1024 * 1024) == 0:
                        elapsed = time.time() - start_time
                        progress = min(100, (elapsed / duration_sec) * 100)
                        throughput_mbps = (total_bytes / (1024 * 1024)) / elapsed if elapsed > 0 else 0
                        
                        if monitor:
                            time_remaining = duration_sec - elapsed
                            hours = int(time_remaining // 3600)
                            minutes = int((time_remaining % 3600) // 60)
                            seconds = int(time_remaining % 60)
                            eta_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                            
                            monitor.update_with_fio_data(f"Progress: {progress:.1f}% | Read: {throughput_mbps:.1f} MB/s | ETA: {eta_str}")
                
            finally:
                # Close all file handles
                for fh in file_handles:
                    fh.close()
            
            elapsed_time = time.time() - start_time
            throughput_mbps = (total_bytes / (1024 * 1024)) / elapsed_time if elapsed_time > 0 else 0
            
            return {
                "jobname": job_name,
                "read": {
                    "bw_bytes": int(total_bytes / elapsed_time) if elapsed_time > 0 else 0,
                    "bw": throughput_mbps,
                    "iops": int((total_bytes / block_size) / elapsed_time) if elapsed_time > 0 else 0,
                    "runtime_msec": int(elapsed_time * 1000)
                },
                "sustained_metrics": {
                    "total_files": num_files,
                    "file_size_gb": test_file_size / (1024 * 1024 * 1024),
                    "block_size_mb": block_size / (1024 * 1024),
                    "total_data_read_gb": total_bytes / (1024 * 1024 * 1024)
                }
            }
        
        except Exception as e:
            if monitor:
                monitor.log_error(f"Sustained read test failed: {e}")
            return None
        finally:
            # Clean up test files
            for file_path in file_paths:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except:
                    pass

    def _run_mixed_test(self, disk_path: str, size_gb: int, duration_sec: int, monitor=None, job_name="mixed_test", read_ratio=0.95) -> Optional[Dict[str, Any]]:
        """Run a mixed read/write test."""
        if monitor:
            monitor.set_test_phase(f"Python: {job_name}", duration_sec)
        
        file_path = os.path.join(disk_path, f"{self.test_file_path}_{job_name}")
        block_size = 4096  # 4KB blocks
        test_file_size = min(size_gb * 1024 * 1024 * 1024, 100 * 1024 * 1024)  # Max 100MB for quick test
        
        try:
            # Create initial test file
            with open(file_path, 'wb') as f:
                for _ in range(test_file_size // block_size):
                    f.write(os.urandom(block_size))
            
            # Mixed read/write operations
            total_read_bytes = 0
            total_write_bytes = 0
            start_time = time.time()
            
            with open(file_path, 'r+b') as f:
                while time.time() - start_time < duration_sec and not self.stop_flag.is_set():
                    if random.random() < read_ratio:
                        # Read operation
                        f.seek(random.randint(0, max(0, test_file_size - block_size)))
                        data = f.read(block_size)
                        total_read_bytes += len(data)
                    else:
                        # Write operation
                        f.seek(random.randint(0, max(0, test_file_size - block_size)))
                        data = os.urandom(block_size)
                        f.write(data)
                        f.flush()
                        total_write_bytes += block_size
                    
                    # Update progress
                    elapsed = time.time() - start_time
                    progress = min(100, (elapsed / duration_sec) * 100)
                    read_mbps = (total_read_bytes / (1024 * 1024)) / elapsed if elapsed > 0 else 0
                    write_mbps = (total_write_bytes / (1024 * 1024)) / elapsed if elapsed > 0 else 0
                    
                    if monitor:
                        monitor.update_with_fio_data(f"Progress: {progress:.1f}% | Read: {read_mbps:.1f} MB/s | Write: {write_mbps:.1f} MB/s")
                    
                    # Small delay to prevent overwhelming the system
                    time.sleep(0.01)
            
            elapsed_time = time.time() - start_time
            read_mbps = (total_read_bytes / (1024 * 1024)) / elapsed_time if elapsed_time > 0 else 0
            write_mbps = (total_write_bytes / (1024 * 1024)) / elapsed_time if elapsed_time > 0 else 0
            
            return {
                "jobname": job_name,
                "read": {
                    "bw_bytes": int(total_read_bytes / elapsed_time) if elapsed_time > 0 else 0,
                    "bw": read_mbps,
                    "iops": int((total_read_bytes / block_size) / elapsed_time) if elapsed_time > 0 else 0,
                    "runtime_msec": int(elapsed_time * 1000)
                },
                "write": {
                    "bw_bytes": int(total_write_bytes / elapsed_time) if elapsed_time > 0 else 0,
                    "bw": write_mbps,
                    "iops": int((total_write_bytes / block_size) / elapsed_time) if elapsed_time > 0 else 0,
                    "runtime_msec": int(elapsed_time * 1000)
                }
            }
        
        except Exception as e:
            if monitor:
                monitor.log_error(f"Mixed test failed: {e}")
            return None
        finally:
            # Clean up test file
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
    
    def stop_test(self):
        """Stop the currently running test."""
        self.stop_flag.set()
    
    def cleanup_test_files(self, disk_path: str):
        """Clean up any remaining test files."""
        try:
            for filename in os.listdir(disk_path):
                if filename.startswith(self.test_file_path):
                    file_path = os.path.join(disk_path, filename)
                    os.remove(file_path)
                    print(f"Cleaned up test file: {file_path}")
        except Exception as e:
            print(f"Error during cleanup: {e}")
