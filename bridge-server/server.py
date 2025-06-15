#!/usr/bin/env python3
"""
QLab Disk Performance Tester - Communication Bridge Server

This server provides a bridge between the web GUI and the diskbench helper binary.
It runs a local HTTP server that accepts requests from the web interface and
executes the appropriate diskbench commands.
"""

import json
import logging
import os
import subprocess
import sys
import threading
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import socketserver

# Add diskbench to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'diskbench'))

class DiskBenchBridge:
    """Bridge between web GUI and diskbench helper binary."""
    
    def __init__(self):
        self.diskbench_path = os.path.join(os.path.dirname(__file__), '..', 'diskbench')
        self.running_tests = {}
        self.logger = logging.getLogger(__name__)
        
    def execute_diskbench_command(self, args):
        """Execute a diskbench command and return the result."""
        try:
            # Build command
            cmd = [sys.executable, 'main.py'] + args
            
            # Execute in diskbench directory
            result = subprocess.run(
                cmd,
                cwd=self.diskbench_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                # Try to parse as JSON if possible
                try:
                    json_result = json.loads(result.stdout)
                    # If JSON parsing succeeds, use the JSON result
                    return json_result
                except json.JSONDecodeError:
                    # If not JSON, return as text
                    return {
                        'success': True,
                        'output': result.stdout,
                        'stderr': result.stderr
                    }
            else:
                return {
                    'success': False,
                    'error': result.stderr or result.stdout,
                    'returncode': result.returncode
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Command timed out after 5 minutes'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def start_test(self, test_params):
        """Start a disk performance test."""
        try:
            # Generate unique test ID
            test_id = f"test_{int(time.time())}"
            
            # Map test types from web GUI to diskbench
            test_type_mapping = {
                'qlab_mixed': 'setup_check',
                'seq_read': 'baseline_streaming',
                'seq_write': 'baseline_streaming', 
                'rand_read': 'setup_check',
                'rand_write': 'setup_check',
                'mixed_workload': 'qlab_prores_422',
                'qlab_prores_hq': 'qlab_prores_hq',
                'qlab_prores_422': 'qlab_prores_422'
            }
            
            diskbench_test_type = test_type_mapping.get(
                test_params.get('test_type', 'setup_check'), 
                'setup_check'
            )
            
            # Build command arguments
            args = [
                '--test', diskbench_test_type,
                '--disk', test_params.get('disk_path', '/tmp'),
                '--size', str(test_params.get('size_gb', 1)),
                '--json'
            ]
            
            # Add output file
            output_file = f"/tmp/diskbench-{test_id}.json"
            args.extend(['--output', output_file])
            
            # Add progress flag
            if test_params.get('show_progress', True):
                args.append('--progress')
            
            # Add verbose flag for debugging
            args.append('--verbose')
            
            # Store test info
            self.running_tests[test_id] = {
                'status': 'starting',
                'start_time': datetime.now().isoformat(),
                'params': test_params,
                'output_file': output_file,
                'progress': 0,
                'diskbench_test_type': diskbench_test_type
            }
            
            # Start test in background thread
            thread = threading.Thread(
                target=self._run_test_thread,
                args=(test_id, args)
            )
            thread.daemon = True
            thread.start()
            
            return {
                'success': True,
                'test_id': test_id,
                'status': 'started',
                'diskbench_test_type': diskbench_test_type
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _run_test_thread(self, test_id, args):
        """Run test in background thread."""
        try:
            self.running_tests[test_id]['status'] = 'running'
            self.logger.info(f"Starting test {test_id} with args: {args}")
            
            # Execute test
            result = self.execute_diskbench_command(args)
            self.logger.info(f"Test {test_id} command result: {result}")
            
            if result.get('success', False):
                # Try to load results from output file
                output_file = self.running_tests[test_id]['output_file']
                try:
                    if os.path.exists(output_file):
                        with open(output_file, 'r') as f:
                            file_results = json.load(f)
                        self.running_tests[test_id]['result'] = file_results
                        self.logger.info(f"Loaded test results from {output_file}")
                    else:
                        # Use command output if file doesn't exist
                        self.running_tests[test_id]['result'] = result
                        self.logger.warning(f"Output file {output_file} not found, using command output")
                except Exception as e:
                    self.logger.error(f"Failed to load results from {output_file}: {e}")
                    self.running_tests[test_id]['result'] = result
                
                self.running_tests[test_id]['status'] = 'completed'
                self.running_tests[test_id]['progress'] = 100
            else:
                self.running_tests[test_id]['status'] = 'failed'
                self.running_tests[test_id]['error'] = result.get('error', 'Unknown error')
                self.logger.error(f"Test {test_id} failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.running_tests[test_id]['status'] = 'failed'
            self.running_tests[test_id]['error'] = str(e)
            self.logger.error(f"Exception in test {test_id}: {e}")
        
        finally:
            self.running_tests[test_id]['end_time'] = datetime.now().isoformat()
    
    def get_test_status(self, test_id):
        """Get status of a running test."""
        if test_id not in self.running_tests:
            return {
                'success': False,
                'error': 'Test not found'
            }
        
        test_info = self.running_tests[test_id].copy()
        
        # Simulate progress for running tests
        if test_info['status'] == 'running':
            elapsed = time.time() - time.mktime(
                datetime.fromisoformat(test_info['start_time']).timetuple()
            )
            # Estimate progress based on elapsed time (rough estimate)
            estimated_duration = 60  # 60 seconds for a typical test
            progress = min(95, (elapsed / estimated_duration) * 100)
            test_info['progress'] = progress
        
        return {
            'success': True,
            'test_info': test_info
        }
    
    def list_disks(self):
        """List available disks."""
        return self.execute_diskbench_command(['--list-disks', '--json'])
    
    def validate_system(self):
        """Validate system requirements."""
        return self.execute_diskbench_command(['--validate', '--json'])
    
    def get_version(self):
        """Get diskbench version."""
        return self.execute_diskbench_command(['--version'])
    
    def detect_system_status(self):
        """Detect system status and FIO availability."""
        return self.execute_diskbench_command(['--detect', '--json'])
    
    def install_fio(self):
        """Install or fix FIO for macOS."""
        return self.execute_diskbench_command(['--install', '--json'])
    
    def validate_setup(self):
        """Run setup validation tests."""
        return self.execute_diskbench_command(['--setup-validate', '--json'])


class BridgeRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the bridge server."""
    
    def __init__(self, *args, bridge=None, **kwargs):
        self.bridge = bridge
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query_params = parse_qs(parsed_url.query)
            
            if path == '/api/disks':
                self._handle_list_disks()
            elif path == '/api/validate':
                self._handle_validate()
            elif path == '/api/version':
                self._handle_version()
            elif path == '/api/status':
                self._handle_status()
            elif path == '/api/setup/validate':
                self._handle_setup_validate()
            elif path.startswith('/api/test/'):
                test_id = path.split('/')[-1]
                self._handle_test_status(test_id)
            elif path == '/':
                self._serve_web_gui()
            elif path.startswith('/web-gui/'):
                self._serve_static_file(path)
            elif path in ['/styles.css', '/app.js']:
                self._serve_static_file(path)
            else:
                self._send_error(404, 'Not Found')
                
        except Exception as e:
            self._send_error(500, str(e))
    
    def do_POST(self):
        """Handle POST requests."""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            if path == '/api/test/start':
                self._handle_start_test()
            else:
                self._send_error(404, 'Not Found')
                
        except Exception as e:
            self._send_error(500, str(e))
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS."""
        self._send_cors_headers()
        self.end_headers()
    
    def _send_cors_headers(self):
        """Send CORS headers."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def _send_json_response(self, data, status_code=200):
        """Send JSON response."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self._send_cors_headers()
        self.end_headers()
        
        json_data = json.dumps(data, indent=2)
        self.wfile.write(json_data.encode('utf-8'))
    
    def _send_error(self, status_code, message):
        """Send error response."""
        self._send_json_response({
            'success': False,
            'error': message
        }, status_code)
    
    def _handle_list_disks(self):
        """Handle disk listing request."""
        result = self.bridge.list_disks()
        self._send_json_response(result)
    
    def _handle_validate(self):
        """Handle system validation request."""
        result = self.bridge.validate_system()
        self._send_json_response(result)
    
    def _handle_version(self):
        """Handle version request."""
        result = self.bridge.get_version()
        self._send_json_response(result)
    
    def _handle_status(self):
        """Handle system status request."""
        result = self.bridge.detect_system_status()
        self._send_json_response(result)
    
    def _handle_setup_validate(self):
        """Handle setup validation request."""
        result = self.bridge.validate_setup()
        self._send_json_response(result)
    
    def _handle_start_test(self):
        """Handle test start request."""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            test_params = json.loads(post_data.decode('utf-8'))
            
            result = self.bridge.start_test(test_params)
            self._send_json_response(result)
            
        except json.JSONDecodeError:
            self._send_error(400, 'Invalid JSON data')
        except Exception as e:
            self._send_error(500, str(e))
    
    def _handle_test_status(self, test_id):
        """Handle test status request."""
        result = self.bridge.get_test_status(test_id)
        self._send_json_response(result)
    
    def _serve_web_gui(self):
        """Serve the main web GUI."""
        web_gui_path = os.path.join(os.path.dirname(__file__), '..', 'web-gui', 'index.html')
        self._serve_file(web_gui_path, 'text/html')
    
    def _serve_static_file(self, path):
        """Serve static files from web-gui directory."""
        # Handle both /web-gui/ prefixed and direct file requests
        if path.startswith('/web-gui/'):
            file_path = path[9:]  # Remove '/web-gui/'
        else:
            file_path = path[1:]  # Remove leading '/'
        
        full_path = os.path.join(os.path.dirname(__file__), '..', 'web-gui', file_path)
        
        # Determine content type
        if file_path.endswith('.css'):
            content_type = 'text/css'
        elif file_path.endswith('.js'):
            content_type = 'application/javascript'
        elif file_path.endswith('.html'):
            content_type = 'text/html'
        else:
            content_type = 'application/octet-stream'
        
        self._serve_file(full_path, content_type)
    
    def _serve_file(self, file_path, content_type):
        """Serve a file with the given content type."""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(content)
            else:
                self._send_error(404, 'File not found')
        except Exception as e:
            self._send_error(500, str(e))
    
    def log_message(self, format, *args):
        """Override to use our logger."""
        logging.info(f"{self.address_string()} - {format % args}")


class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    """Threaded HTTP server for handling multiple requests."""
    allow_reuse_address = True


def create_request_handler(bridge):
    """Create a request handler with the bridge instance."""
    def handler(*args, **kwargs):
        return BridgeRequestHandler(*args, bridge=bridge, **kwargs)
    return handler


def main():
    """Main server function."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    # Create bridge instance
    bridge = DiskBenchBridge()
    
    # Create server
    server_address = ('localhost', 8080)
    handler_class = create_request_handler(bridge)
    
    try:
        httpd = ThreadedHTTPServer(server_address, handler_class)
        
        logger.info(f"Starting QLab Disk Performance Tester Bridge Server")
        logger.info(f"Server running at http://{server_address[0]}:{server_address[1]}")
        logger.info(f"Web GUI available at http://{server_address[0]}:{server_address[1]}/")
        logger.info(f"Press Ctrl+C to stop the server")
        
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
