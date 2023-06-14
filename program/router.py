import os
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pyroute2 import IPRoute
import socket

# Global variable
# Server Config

# # Run in Mininet
# hostName = "fcff:1::1"
# serverPort = 8080

# Run on Single Machine
hostName = "localhost"
serverPort = 8000

# Netlink socket
ip_route = IPRoute()
ip_route.bind()

# Cahche of the resolved interface
interfaces = [x.get_attr('IFLA_IFNAME') for x in ip_route.get_links()]
idxs = {}



function = {
    "add_table" : 0,
    "src_route" : 1,
    "dst_route" : 2,
}

""" Example POST structure

    {
        "command" : [
            {
                "function" : "table", // required
                "table" : 250,      // required
                "detail" : {
                    "op" : "add"
                    "device" : "r1-r2",
                    "destination : "fd00::/32",
                    "encapmode" : "encap",
                    "segments" : [
                        "fcff:3::1",
                        "fcff:4::100"
                    ]
                } 
            }
        ]
    }

    {
        "command" : [
            {
                "function" : "add_src_route", // required
                "table" : "ids_app"          // required
                "detail" : {
                    "op" : "add"
                    "addr" : "fd00:0:14::2"
                    "priority" : 32005
                }
                
            }
        ]
    }
"""





class MyServer(BaseHTTPRequestHandler):

    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            content = json.loads(self.rfile.read(content_length).decode())
            for command in content["command"]:
                print(command)
                if(command["function"] == "table"):
                    ip_route.route(command["detail"]["op"], dst=command["detail"]["destination"],oif=idxs[command["detail"]["device"]], encap={'type':'seg6','mode':command["detail"]["encapmode"],'segs':command["detail"]["segments"]}, table=command["table"])
                    print("ids_app")
                elif(command["function"] == "src_route"):
                    ip_route.rule(command["detail"]["op"], table=command["table"], priority=command["detail"]["priority"],src=command["detail"]["addr"])
                elif(command["function"] == "dst_route"):
                    ip_route.rule(command["detail"]["op"], table=command["table"], priority=command["detail"]["priority"],dst=command["detail"]["addr"])
            
            self._set_response()
            self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))
        except Exception as e:
            print("An error occured")
            print(type(e))
            print(e.args)
            print(e)
            self.send_response(500)
    
class HTTPServerV6(HTTPServer):
    address_family = socket.AF_INET6

if __name__ == "__main__":

    for interface in interfaces:
        idxs[interface] = ip_route.link_lookup(ifname=interface)[0]
    print(idxs)
    # For IPv4
    webServer = HTTPServer((hostName, serverPort), MyServer)
    # For IPv6
    # webServer = HTTPServerV6((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass
    
    webServer.serve_close()
    print("Server stopped.")
