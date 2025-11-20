import unittest
import urllib.request
import urllib.error
import subprocess
import time
import sys
import os
import signal
import json
from typing import Any, Dict, Optional

# Configuration
SERVER_PORT = 8765
BASE_URL = f"http://127.0.0.1:{SERVER_PORT}"
SERVER_SCRIPT = os.path.join(os.path.dirname(__file__), '..', 'bridge-server', 'server.py')

class TestBridgeServerIntegration(unittest.TestCase):
    server_process: Optional[subprocess.Popen] = None

    @classmethod
    def setUpClass(cls) -> None:
        """Start the bridge server before running tests."""
        print(f"Starting bridge server from {SERVER_SCRIPT}...")
        # Ensure we use the same python interpreter
        cls.server_process = subprocess.Popen(
            [sys.executable, SERVER_SCRIPT],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to start
        max_retries = 20
        for i in range(max_retries):
            try:
                with urllib.request.urlopen(f"{BASE_URL}/api/status", timeout=1) as response:
                    if response.status == 200:
                        print("Server started successfully.")
                        return
            except (urllib.error.URLError, ConnectionResetError) as e:
                print(f"Connection attempt {i+1} failed: {e}")
                time.sleep(1.0)
        
        # If we get here, server failed to start
        # Check if process is still running
        if cls.server_process.poll() is not None:
            stdout, stderr = cls.server_process.communicate()
            print(f"Server process exited early. RC={cls.server_process.returncode}")
            print(f"Stdout: {stdout}")
            print(f"Stderr: {stderr}")
        else:
            print("Server process is running but not responding.")
            cls.server_process.terminate()
            
        raise RuntimeError("Could not start bridge server")

    @classmethod
    def tearDownClass(cls) -> None:
        """Stop the bridge server after tests."""
        if cls.server_process:
            print("Stopping bridge server...")
            cls.server_process.terminate()
            try:
                cls.server_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                cls.server_process.kill()

    def _get_json(self, endpoint: str) -> Dict[str, Any]:
        """Helper to perform GET request and return JSON."""
        url = f"{BASE_URL}{endpoint}"
        with urllib.request.urlopen(url, timeout=5) as response:
            self.assertEqual(response.status, 200)
            data = response.read().decode('utf-8')
            return json.loads(data)

    def test_system_status(self) -> None:
        """Test the system status endpoint."""
        data = self._get_json("/api/status")
        self.assertIn('status', data)

    def test_list_disks(self) -> None:
        """Test the list disks endpoint."""
        data = self._get_json("/api/disks")
        self.assertIn('disks', data)
        self.assertIsInstance(data['disks'], list)

    def test_list_tests(self) -> None:
        """Test the list tests endpoint."""
        data = self._get_json("/api/tests")
        self.assertIn('tests', data)
        self.assertIn('order', data)
        self.assertTrue(len(data['order']) > 0)

    def test_invalid_endpoint(self) -> None:
        """Test accessing an invalid endpoint."""
        url = f"{BASE_URL}/api/invalid"
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(url, timeout=5)
        self.assertEqual(cm.exception.code, 404)

if __name__ == '__main__':
    unittest.main()
