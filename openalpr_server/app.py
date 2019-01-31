#!/usr/bin/python3
# Waslley Souza (waslleys@gmail.com)
# 2018

import os
import json
import base64
from oraclecloud import Storage
#from sinesp_client import SinespClient
from http.server import BaseHTTPRequestHandler, HTTPServer


PORT_NUMBER = int(os.environ.get('PORT', 8084))
STORAGE_USER = os.environ.get('STORAGE_USER')
STORAGE_PASS = os.environ.get('STORAGE_PASS')
STORAGE_IDENTITY = os.environ.get('STORAGE_IDENTITY')


class MyServer(BaseHTTPRequestHandler):

    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
 
    def do_HEAD(self):
        self._set_headers()
        return

    def do_GET(self):
        self._set_headers()
        self.wfile.write(bytes("<html><head><meta http-equiv='refresh' content='10'></head><body>", "utf8"))

        if len(list) > 0:
            data = list[-1]['payload']['data']
            picture = data['picture']
            picture_container = picture.split("/")[-2]
            picture_name = picture.split("/")[-1]

            _, file = storage.get_object_content_and_metadata(picture_container, picture_name)
            img = base64.b64encode(file).decode()
            
            self.wfile.write(bytes(json.dumps(data), "utf8"))
            self.wfile.write(bytes("<br><br>", "utf8"))
            self.wfile.write(bytes("<img src='data:image/png;base64," + img + "' />", "utf8"))

            #self.wfile.write(bytes("<br><br>", "utf8"))
            #result = sc.search(data['license_plate'])
            #self.wfile.write(bytes(result, "utf8"))

        self.wfile.write(bytes("</body></html>", "utf8"))
        return

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        list.append(json.loads(post_data)[0])
        self._set_headers()
        return

    def do_PUT(self):
        list = []
        self._set_headers()
        return
 
def run():
    print('starting server...')
    server_address = ('0.0.0.0', PORT_NUMBER)
    httpd = HTTPServer(server_address, MyServer)
    print('running server...')
    httpd.serve_forever()
  
if __name__ == "__main__":
    storage = Storage(STORAGE_USER, STORAGE_PASS, STORAGE_IDENTITY)
    #sc = SinespClient()
    list = []    
    run()