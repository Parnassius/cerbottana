from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import threading

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

  def do_GET(self): # pylint: disable=invalid-name
    self.send_response(200)
    self.end_headers()
    self.wfile.write(b'cerbottana')

  def do_HEAD(self): # pylint: disable=invalid-name
    self.send_response(200)
    self.end_headers()

class Server:
  def __init__(self):
    self.httpd = HTTPServer(('', int(os.environ['PORT'])), SimpleHTTPRequestHandler)
    self.httpdthread = None

  def listen(self):
    self.httpdthread = threading.Thread(target=self.httpd.serve_forever)
    self.httpdthread.start()

  def dummy(self):
    pass
