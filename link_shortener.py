"""Server HTTP sederhana untuk menyimpan dan mengalihkan nama pendek ke URI panjang."""

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, unquote
import requests

# from html import escape

FORM = """<!DOCTYPE html>
  <title>Message Board</title>
  <form method="POST">
    <label>Long URI:
      <input type="text" name="longuri"></input>
    <label>
    <br>
    <label>Short name:
      <input type="text" name="shortname"></input>
    </label>
    <br>
    <button type="submit">Save</button>
  </form>
  <p>URIs I know about:</p>
  <pre>
  {}
  </pre>
"""

memory = {}


def check_uri(uri, timeout=5):
    """
    Check whether this URI is reachable, i.e. does it return a 200 OK?"""
    try:
        r = requests.get(uri, timeout=timeout)
        # If the GET request returns, was it a 200 OK?
        return r.status_code == 200
    except requests.RequestException:
        # If the GET request raised an exception, it's not OK.
        return False


class LinkShortener(BaseHTTPRequestHandler):
    """Handle HTTP requests for creating and resolving short links."""

    def do_GET(self):
        # A GET request will either be for / (the root path) or for /some-name.
        # Strip off the / and we have either empty string or a name.
        
        
        shortname = unquote(self.path[1:])

        if shortname:
            if shortname in memory:
                self.send_response(303)
                self.send_header("Location", memory[shortname])
                self.end_headers()
            else:
                self.send_response(404)
                self.send_header("Content-type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(f"I don't know {shortname}.".encode())
        else:
            # Root path. Send the form.
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            # My own way
            # message = form + "\n"
            # for name in memory:
            #   message += name + ' ' + memory[name] + "\n"
            # known = "\n".join(
            #     "{} : {}".format(key, memory[key]) for key in memory.keys()
            # )
            known = "\n".join(f"{key} : {memory[key]}" for key in memory)
            self.wfile.write(FORM.format(known).encode())

    def do_POST(self):
        # How long was the message? (Use the Content-Length header.)
        length = int(self.headers.get("Content-length", 0))

        # Read the correct amount of data from the request and decode it
        body = self.rfile.read(length).decode()
        # print(data)
        params = parse_qs(body)
        # Escape HTML tags in the message so users can't break world+dog.
        # params = escape(params)

        if "longuri" not in params or "shortname" not in params:
            # Extract the "longuri" and "shortname"  fields from the request data.
            self.send_response(400)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("Error 400: Bad request!".encode())
            return

        longuri = params["longuri"][0]
        shortname = params["shortname"][0]

        if check_uri(longuri):
            # This URI is good!  Remember it under the specified name.
            memory[shortname] = longuri

            # Serve a redirect to the root page (the form).
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()
        else:
            self.send_response(404)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("Error 404: Not found!".encode())


if __name__ == "__main__":
    try:
        server_address = ("", 8000)  # Serve on all addresses, port 8000
        httpd = HTTPServer(server_address, LinkShortener)
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Keyboard interruption. The program is stopped by user!")
