import os
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

hostName = "localhost"
serverPort = 8080

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            self.path = 'example'
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(exact_src_addr()).encode())
        except Exception as e:
            print("An error occured")
            print(type(e))
            print(e.args)
            print(e)
            self.send_response(500)

def exact_src_addr(path="/var/log/snort/alert_json.txt"):
    f = open(path, "r")
    data = [json.loads(line) for line in open(path, "r")]
    data.reverse()
    data = [{"time_seconds" : time.time() - entry["seconds"],"src_addr" : entry["src_addr"]} for entry in data]

    ## Remove duplicate src_addr
    format_data = delete_duplicates(data, "src_addr")
    return format_data

def delete_duplicates(lst, key):
    unique_dicts = []
    unique_keys = []
    
    for dct in lst:
        value = dct.get(key)
        if value not in unique_keys:
            unique_keys.append(value)
            unique_dicts.append(dct)
    
    return unique_dicts




if __name__ == "__main__":
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass
    
    webServer.serve_close()
    print("Server stopped.")