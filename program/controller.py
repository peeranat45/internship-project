import os
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from http.client import HTTPConnection
import socket

# # Run in Mininet
# hostName = "fcff:4::1"
# serverPort = 8080

# routerName = 'fcff:1::1' # for testing only
# routerPort = 8080

# Run on Single Machine
hostName = "localhost"
serverPort = 8080

routerName = "localhost"
routerPort = 8000


# Mapping Application
tables =  {
    "ids_app" : 250,
    "firewall_app" : 251,
    "directly_route": 252
}

"""
For IDS APP /policy
{
    "command" : [
        {
            "app" : "ids_app",
            "op" : "add" | "del",
            "src_addr" : "fd00:0:14::2/128"
        }
    ]
}
        |
        |
        V

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

/paths

{
    "command" : [
        {
            "app" : "ids_app",
            "op" : "add",
            "segments" : [
                    "fcff:3::1",
                    "fcff:4::100"
            ]
        },
    ]
}

        
    |
    |
    V

{
    "command" : [
        {
            "function" : "table",
            "table" : "ids_app",
            "detail" : {
                "op" : "add",
                "device" : "veth1",
                "destination" : "fd00::/32",
                "encapmode" : "encap",
                "segments" : [
                    "fcff:3::1",
                    "fcff:4::100"
                ]
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
            print(content)
            commands = []
            if self.path == "/paths":
                for command in content["command"]:
                    temp = {}
                    temp["function"] = "table"
                    temp["table"] = tables[command["app"]]
                    temp["detail"] = {
                        "op" : command["op"],
                        "device" : "lo", # changed when delployed
                        "destination" : "fd00::/32",
                        "encapmode" : "encap",
                        "segments" : command["segments"]
                    }

                    commands.append(temp)

            elif self.path == "/policy":
                for command in content["command"]:
                    temp = {}
                    temp["detail"] = {
                        "op" : command["op"],
                        "priority" : 32005
                    } 
                    if "src_addr" in command:
                        temp["function"] = "src_route"
                        temp["detail"]["addr"] = command["src_addr"]
                    elif "dst_addr" in command:
                        temp["function"] = "dst_route"
                        temp["detail"]["addr"] = command["dst_addr"]

                    temp["table"] = tables[command["app"]]
                    commands.append(temp)
            
            loads = {"command" : commands}
            print(loads)
            con = HTTPConnection(routerName,routerPort,timeout=10)
            headers = {"Content-type" : 'application/json'}
            print("fuck")
            con.request('POST', '/', json.dumps(loads).encode(), headers)
            response = con.getresponse()
            print(response.read().decode())
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
