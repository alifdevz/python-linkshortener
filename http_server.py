from http.server import HTTPServer, BaseHTTPRequestHandler

class MyHTTPServer(BaseHTTPRequestHandler):
  def do_GET(self):
    self.send_response(200)
    self.send_header("Content-type", "text/plain; charset=utf-8")
    self.end_headers()

    self.wfile.write("Hello, this is from MyHTTPServer".encode())

if __name__ == '__main__':
  server_address = ('', 8000) # Serve on all addresses, port 8000
  httpd = HTTPServer(server_address, MyHTTPServer)
  httpd.serve_forever()
