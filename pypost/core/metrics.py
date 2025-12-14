import threading
from wsgiref.simple_server import make_server
from prometheus_client import make_wsgi_app, CollectorRegistry, Counter, Summary

class MetricsManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(MetricsManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.registry = CollectorRegistry()
        self.server = None
        self.thread = None
        self.server_lock = threading.Lock()
        
        # Define metrics
        self._init_metrics()

    def _init_metrics(self):
        """Initialize all Prometheus metrics."""
        self.gui_send_clicks = Counter(
            'gui_send_clicks_total', 
            'Number of times Send button was clicked',
            registry=self.registry
        )
        
        self.requests_sent = Counter(
            'requests_sent_total',
            'Number of HTTP requests sent',
            ['method'],
            registry=self.registry
        )
        
        self.responses_received = Counter(
            'responses_received_total',
            'Number of HTTP responses received',
            ['method', 'status_code'],
            registry=self.registry
        )
        
        self.mcp_requests_received = Counter(
            'mcp_requests_received_total',
            'Number of requests received by MCP server',
            ['method'],
            registry=self.registry
        )
        
        self.mcp_responses_sent = Counter(
            'mcp_responses_sent_total',
            'Number of responses sent by MCP server',
            ['method', 'status'],
            registry=self.registry
        )

    def start_server(self, host: str, port: int):
        """Start the Prometheus metrics server."""
        with self.server_lock:
            if self.server:
                self.stop_server()
            
            try:
                prometheus_app = make_wsgi_app(registry=self.registry)
                
                def app_wrapper(environ, start_response):
                    if environ['PATH_INFO'] == '/metrics':
                        return prometheus_app(environ, start_response)
                    else:
                        start_response('404 Not Found', [('Content-Type', 'text/plain')])
                        return [b'Not Found']

                self.server = make_server(host, port, app_wrapper)
                self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
                self.thread.start()
                print(f"Metrics server started on {host}:{port}")
            except Exception as e:
                print(f"Failed to start metrics server: {e}")

    def stop_server(self):
        """Stop the Prometheus metrics server."""
        if self.server:
            try:
                self.server.shutdown()
                self.server.server_close()
            except Exception as e:
                print(f"Error stopping metrics server: {e}")
            finally:
                if self.thread:
                    self.thread.join(timeout=1.0)
                self.server = None
                self.thread = None
                print("Metrics server stopped")

    def restart_server(self, host: str, port: int):
        """Restart the metrics server with new settings."""
        self.stop_server()
        self.start_server(host, port)

    # Tracking methods
    def track_gui_send_click(self):
        self.gui_send_clicks.inc()

    def track_request_sent(self, method: str):
        self.requests_sent.labels(method=method).inc()

    def track_response_received(self, method: str, status_code: str):
        self.responses_received.labels(method=method, status_code=status_code).inc()

    def track_mcp_request_received(self, method: str):
        self.mcp_requests_received.labels(method=method).inc()

    def track_mcp_response_sent(self, method: str, status: str):
        self.mcp_responses_sent.labels(method=method, status=status).inc()
