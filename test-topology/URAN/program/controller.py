import os, sys
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from http.client import HTTPConnection
import socket
import argparse
from ipaddress import ip_address, IPv6Address
from pyroute2 import IPRoute
from dotenv import load_dotenv





load_dotenv()
CON_ROUTER=str(os.getenv('CON_ROUTER'))
EGR_ROUTER=str(os.getenv('EGR_ROUTER'))
IDS_ADDR=str(os.getenv('IDS_ADDR'))
HOST_SOURCE=str(os.getenv('HOST_SOURCE'))
HOST_DST=str(os.getenv('HOST_DST'))
IDS_APP=str(os.getenv('IDS_APP'))
ING_ROUTER=str(os.getenv('ING_ROUTER'))

# # Run in Mininet
hostName = CON_ROUTER
serverPort = 8080

routerName = ING_ROUTER # for testing only
routerPort = 8080

# Run on Single Machine
#hostName = "localhost"
#serverPort = 8080

#routerName = "localhost"
#routerPort = 8000

ip_route = IPRoute()
ip_route.bind()

# Mapping Application
tables =  {
    "ids_app" : 250,
    "firewall_app" : 251,
    "directly_route": 252
}

priority = 1000

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
            con1 = HTTPConnection(routerName, routerPort, timeout=10)
            con1.request('GET', '/interfaces')
            interface_router = json.loads(con1.getresponse().read().decode())
            print(interface_router)
            print(content)
            commands = []
            print(HOST_DST)
            if self.path == "/paths":
                for command in content["command"]:
                    temp = {}
                    temp["function"] = "table"
                    temp["table"] = tables[command["app"]]
                    temp["detail"] = {
                        "op" : command["op"],
                        "device" : interface_router["interfaces"][-1], # changed when delployed
                        "destination" : HOST_DST, # Please change this for each destination ping test
                        "encapmode" : "encap",
                        "segments" : command["segments"]
                    }

                    commands.append(temp)

            elif self.path == "/policy":
                for command in content["command"]:
                    temp = {}
                    temp["detail"] = {
                        "op" : command["op"],
                        "priority" : 100 if command["app"] == "directly_route" else 1000
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
    
    def do_GET(self):
        try:
            if(self.path == "/rules"):
                con = HTTPConnection(routerName,routerPort,timeout=10)
                con.request('GET', '/rules')
                res = json.loads(con.getresponse().read().decode())
                
                
                # print(res)
                for data in res["data"]:
                    print(data)
                    if "FRA_DST" in data:
                        data["addrType"] = "dst"
                        data["addr"] = data["FRA_DST"]
                        del data["FRA_DST"]
                    elif "FRA_SRC" in data:
                        data["addrType"] = "src"
                        data["addr"] = data["FRA_SRC"]
                        del data["FRA_SRC"]
            
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()

                self.wfile.write(json.dumps(res).encode('utf-8'))
            
        except Exception as e:
            print("An error occured")
            print(type(e))
            print(e.args)
            print(e)
            self.send_response(500)


def argument_parser():
    # Argument parser

    # parser = argparse.ArgumentParser(prog='SDN Controller')
    # parser.add_argument('routerAddress')
    # parser.add_argument('-rp', type=int)
    # parser.add_argument('-cp', type=int)

    # args = parser.parse_args()

    # if args.rp != None:
    #     routerPort = args.rp
    # if args.cp != None:
    #     serverPort = args.cp

    # def validIPAddress(IP: str) -> str:
    #     try:
    #         return True if type(ip_address(IP)) is IPv6Address else False
    #     except ValueError:
    #         sys.exit("Invalid IP")

    # print(validIPAddress(args.routerAddress))

    routerPort = 8080
    serverPort = 8080

class HTTPServerV6(HTTPServer):
    address_family = socket.AF_INET6

# def assignDefaultPath():


if __name__ == "__main__":
    argument_parser()
    # For IPv4
    #webServer = HTTPServer((hostName, serverPort), MyServer)
    # For IPv6

    hostName = ip_route.get_addr()[1]["attrs"][0][1]
    webServer = HTTPServerV6((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass
    
    webServer.serve_close()
    print("Server stopped.")


