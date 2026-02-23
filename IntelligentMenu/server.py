import http.server
import socketserver
import os
import urllib.request
import urllib.parse
import json

PORT = 5000
BACKEND_URL = 'http://localhost:8000'

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory='.', **kwargs)
    
    def do_GET(self):
        # Handle API proxy requests
        if self.path.startswith('/api/'):
            self.proxy_to_backend()
            return
        
        # Serve index.html when accessing root
        if self.path == '/':
            self.path = '/public/index.html'
        return super().do_GET()
    
    def do_POST(self):
        # Handle API proxy requests
        if self.path.startswith('/api/'):
            self.proxy_to_backend()
            return
        
        return super().do_POST()
    
    def do_OPTIONS(self):
        # Handle preflight requests
        self.send_response(200)
        self.end_headers()
    
    def proxy_to_backend(self):
        try:
            # Remove /api prefix and construct backend URL
            backend_path = self.path[4:]  # Remove '/api'
            backend_url = f"{BACKEND_URL}{backend_path}"
            
            # Get request body for POST requests
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else None
            
            # Create request
            req = urllib.request.Request(backend_url, data=post_data)
            
            # Copy headers
            if post_data:
                req.add_header('Content-Type', 'application/json')
            
            # Make request to backend
            with urllib.request.urlopen(req) as response:
                # Send response status
                self.send_response(response.getcode())
                
                # Copy response headers
                for header, value in response.headers.items():
                    if header.lower() not in ['content-encoding', 'transfer-encoding']:
                        self.send_header(header, value)
                
                self.end_headers()
                
                # Copy response body
                self.wfile.write(response.read())
                
        except Exception as e:
            print(f"Proxy error: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = json.dumps({"error": "Backend connection failed"})
            self.wfile.write(error_response.encode())
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

if __name__ == "__main__":
    with socketserver.TCPServer(("0.0.0.0", PORT), MyHTTPRequestHandler) as httpd:
        print(f"Frontend server running at http://0.0.0.0:{PORT}")
        print("Serving files from current directory")
        httpd.serve_forever()