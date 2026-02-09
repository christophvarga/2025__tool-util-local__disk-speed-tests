"""HTTP request handler: CORS, JSON responses, routing, static file serving."""
import json, logging, os, sys, socketserver
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from validation import _sanitize_error

class BridgeRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the bridge server."""

    def __init__(self, *args, bridge=None, **kwargs):
        self.bridge = bridge
        super().__init__(*args, **kwargs)

    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        if path == '/api/fio-info':
            self._handle_fio_info()
            return
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query_params = parse_qs(parsed_url.query)

            routes = {
                '/api/disks': self._handle_list_disks,
                '/api/validate': self._handle_validate,
                '/api/version': self._handle_version,
                '/api/tests': self._handle_list_tests,
                '/api/status': self._handle_status,
                '/api/setup/validate': self._handle_setup_validate,
                '/api/test-fio': self._handle_test_fio,
                '/api/test-direct-fio': self._handle_direct_fio_test,
                '/api/fio/detect-shm': self._handle_detect_fio_shm,
                '/api/fio/auto-fix': self._handle_auto_fix_fio,
                '/api/background-tests': self._handle_background_tests_status,
                '/api/test/current': self._handle_current_test,
            }
            handler = routes.get(path)
            if handler:
                handler()
            elif path.startswith('/api/test/'):
                self._handle_test_status(path.split('/')[-1])
            elif path == '/':
                self._serve_web_gui()
            elif path.startswith('/web-gui/'):
                self._serve_static_file(path)
            elif path in ['/styles.css', '/app.js']:
                self._serve_static_file(path)
            else:
                self._send_error(404, 'Not Found')
        except Exception as e:
            self._send_error(500, _sanitize_error(e))

    def do_POST(self):
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(length) if length > 0 else b''

            if path == '/api/test/start':
                self._handle_start_test()
            elif path.startswith('/api/test/stop/'):
                self._handle_stop_test(path.split('/')[-1])
            elif path == '/api/test/stop-all':
                self._handle_stop_all_tests()
            elif path.startswith('/api/test/cleanup-background/'):
                self._handle_cleanup_background_test(path.split('/')[-1])
            elif path == '/api/test/cleanup-all-background':
                self._handle_cleanup_all_background_tests()
            elif path == '/api/setup':
                self._handle_setup_action()
            elif path == '/api/validate':
                self._handle_validate_action()
            else:
                self._send_error(404, f'Unknown POST endpoint: {path}')
        except Exception as e:
            logging.getLogger(__name__).error(f"POST handler error: {e}")
            self._send_error(500, _sanitize_error(e))

    def do_OPTIONS(self):
        self._send_cors_headers()
        self.end_headers()

    def _send_cors_headers(self):
        """Send CORS headers restricted to localhost origins (C-5)."""
        origin = self.headers.get('Origin', '')
        if origin and (
            origin.startswith('http://localhost:')
            or origin.startswith('http://127.0.0.1:')
            or origin == 'http://localhost'
            or origin == 'http://127.0.0.1'
        ):
            self.send_header('Access-Control-Allow-Origin', origin)
        else:
            self.send_header('Access-Control-Allow-Origin', 'http://localhost')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def _send_json_response(self, data, status_code=200):
        try:
            self.send_response(status_code)
            self.send_header('Content-Type', 'application/json')
            self._send_cors_headers()
            self.end_headers()
            try:
                json_data = json.dumps(data, indent=2, default=self._json_serializer)
                self.wfile.write(json_data.encode('utf-8'))
            except (TypeError, ValueError) as e:
                err = {'success': False, 'error': f'JSON serialization error: {e}',
                       'data_type': str(type(data))}
                self.wfile.write(json.dumps(err, indent=2).encode('utf-8'))
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            try:
                err = {'success': False, 'error': f'Response generation failed: {e}'}
                self.wfile.write(json.dumps(err).encode('utf-8'))
            except Exception:
                self.wfile.write(
                    b'{"success": false, "error": "Critical response error"}'
                )

    def _json_serializer(self, obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        elif isinstance(obj, bytes):
            return obj.decode('utf-8', errors='replace')
        return str(obj)

    def _send_error(self, status_code, message):
        self._send_json_response({'success': False, 'error': message}, status_code)

    # ----- GET route handlers -----
    def _handle_list_disks(self):
        self._send_json_response(self.bridge.list_disks())

    def _handle_validate(self):
        self._send_json_response(self.bridge.validate_system())

    def _handle_version(self):
        self._send_json_response(self.bridge.get_version())

    def _handle_list_tests(self):
        result = self.bridge.execute_diskbench_command(['--list-tests', '--json'])
        if isinstance(result, dict) and 'tests' in result and 'order' in result:
            self._send_json_response({'success': True, **result})
        else:
            self._send_json_response({'success': True, 'tests': result, 'order': []})

    def _handle_status(self):
        self._send_json_response(self.bridge.detect_system_status())

    def _handle_setup_validate(self):
        self._send_json_response(self.bridge.validate_setup())

    def _handle_test_fio(self):
        self._send_json_response(self.bridge.test_fio_functionality())

    def _handle_direct_fio_test(self):
        parsed = urlparse(self.path)
        qp = parse_qs(parsed.query)
        tp = {}
        if 'size' in qp:
            tp['size'] = qp['size'][0]
        if 'rw' in qp:
            tp['rw'] = qp['rw'][0]
        if 'target_path' in qp:
            tp['target_path'] = qp['target_path'][0]
        if 'duration' in qp:
            try:
                tp['duration'] = int(qp['duration'][0])
            except ValueError:
                pass
        self._send_json_response(self.bridge.run_direct_fio_test(tp))

    def _handle_detect_fio_shm(self):
        self._send_json_response(self.bridge.detect_fio_shm_support())

    def _handle_auto_fix_fio(self):
        self._send_json_response(self.bridge.auto_fix_fio_shm())

    def _handle_fio_info(self):
        try:
            info = self.bridge._verify_fio()
            self._send_json_response({'success': True, 'fio': info})
        except OSError as e:
            self._send_json_response({'success': False, 'error': str(e)})

    def _handle_background_tests_status(self):
        self._send_json_response(self.bridge.get_background_tests_status())

    def _handle_current_test(self):
        self._send_json_response(self.bridge.get_current_test())

    def _handle_test_status(self, test_id):
        self._send_json_response(self.bridge.get_test_status(test_id))

    # ----- POST route handlers -----
    def _handle_start_test(self):
        try:
            cl = int(self.headers['Content-Length'])
            data = json.loads(self.rfile.read(cl).decode('utf-8'))
            self._send_json_response(self.bridge.start_test(data))
        except json.JSONDecodeError:
            self._send_error(400, 'Invalid JSON data')
        except Exception as e:
            self._send_error(500, _sanitize_error(e))

    def _handle_stop_test(self, test_id):
        self._send_json_response(self.bridge.stop_test(test_id))

    def _handle_stop_all_tests(self):
        self._send_json_response(self.bridge.stop_all_tests())

    def _handle_cleanup_background_test(self, test_id):
        self._send_json_response(self.bridge.cleanup_background_test(test_id))

    def _handle_cleanup_all_background_tests(self):
        self._send_json_response(self.bridge.cleanup_all_background_tests())

    def _handle_setup_action(self):
        self._dispatch_post_action(
            {'install_fio': lambda: self.bridge.install_fio()}, 'setup')

    def _handle_validate_action(self):
        self._dispatch_post_action(
            {'run_all_tests': lambda: self.bridge.validate_setup()}, 'validation')

    def _dispatch_post_action(self, action_map, label):
        try:
            cl = int(self.headers['Content-Length'])
            data = json.loads(self.rfile.read(cl).decode('utf-8'))
            action = data.get('action', '')
            handler = action_map.get(action)
            if handler:
                self._send_json_response(handler())
            else:
                self._send_error(400, f'Unknown {label} action: {action}')
        except json.JSONDecodeError:
            self._send_error(400, 'Invalid JSON data')
        except Exception as e:
            self._send_error(500, _sanitize_error(e))

    # ----- static file serving -----
    def _serve_web_gui(self):
        base_dir = getattr(sys, '_MEIPASS', None)
        if base_dir and os.path.isdir(os.path.join(base_dir, 'web-gui')):
            path = os.path.join(base_dir, 'web-gui', 'index.html')
        else:
            path = os.path.join(os.path.dirname(__file__), '..', 'web-gui', 'index.html')
        self._serve_file(path, 'text/html')

    def _serve_static_file(self, url_path):
        if url_path.startswith('/web-gui/'):
            file_path = url_path[9:]
        else:
            file_path = url_path[1:]
        base_dir = getattr(sys, '_MEIPASS', None)
        if base_dir and os.path.isdir(os.path.join(base_dir, 'web-gui')):
            full = os.path.join(base_dir, 'web-gui', file_path)
        else:
            full = os.path.join(os.path.dirname(__file__), '..', 'web-gui', file_path)
        ct_map = {'.css': 'text/css', '.js': 'application/javascript', '.html': 'text/html'}
        ct = ct_map.get(os.path.splitext(file_path)[1], 'application/octet-stream')
        self._serve_file(full, ct)

    def _serve_file(self, file_path, content_type):
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
            self._send_error(500, _sanitize_error(e))

    def log_message(self, format, *args):
        logging.info(f"{self.address_string()} - {format % args}")


class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    """Threaded HTTP server for handling multiple requests."""
    allow_reuse_address = True


def create_request_handler(bridge):
    """Create a request handler with the bridge instance."""
    def handler(*args, **kwargs):
        return BridgeRequestHandler(*args, bridge=bridge, **kwargs)
    return handler
