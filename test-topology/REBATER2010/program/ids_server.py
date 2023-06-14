import os
import json
import time, xmltodict
from http.server import BaseHTTPRequestHandler, HTTPServer
import socket
from pyroute2 import IPRoute
import subprocess

from dotenv import load_dotenv

load_dotenv()
TOPO_FILE=str(os.getenv('TOPO_FILE'))
BW_KEY = int(os.getenv('BW_KEY'))
NODE_NUM = int(os.getenv('HOST_NODE'))
BW_KEY_VALUE=int(os.getenv('BW_KEY_VALUE'))
BW_KEY_SCALE=os.getenv('BW_KEY_SCALE')
CON_ROUTER=str(os.getenv('CON_ROUTER'))
EGR_ROUTER=str(os.getenv('EGR_ROUTER'))
IDS_ADDR=str(os.getenv('IDS_ADDR'))
HOST_SOURCE=str(os.getenv('HOST_SOURCE'))
HOST_DST=str(os.getenv('HOST_DST'))
IDS_APP=str(os.getenv('IDS_APP'))
ING_ROUTER=str(os.getenv('ING_ROUTER'))

ip_route = IPRoute()
ip_route.bind()

#hostName = "localhost"
#serverPort = 9000

hostName = "localhost"
serverPort = 8080

def getIDSInterface():
    with open("./../"+TOPO_FILE) as xml_file:
        data_dict = xmltodict.parse(xml_file.read())
        json_data = json.dumps(data_dict)
        dict_data = json.loads(json_data)
        # print(json_data)
        # print(dict_data["graphml"]["graph"].keys())
        # for i in dict_data["graphml"]["graph"]["node"]:
            # print(i)
        # for i in dict_data["graphml"]["graph"]["edge"]:
            # print(i)
    # print(dict_data)
    def findDictWithKey(listDict, key, value):
        for i in listDict:
            if(i[key] == value):
                return i
        return {'#text' : '0'}
    
    def isEdgeRouter(routerID, edgeRouter):
        for i in edgeRouter:
            if i["routerID"] ==  routerID:
                return True
        return False

    # Preparing data"
    router = [{"id" : int(entry["@id"]) + 1, "name" : entry["data"][-1]["#text"]} for entry in dict_data["graphml"]["graph"]["node"]] 
    link = [{"source": int(entry["@source"]) + 1, "target": int(entry["@target"]) + 1, "bw" : findDictWithKey(entry["data"], '@key', 'd' + str(BW_KEY_VALUE))["#text"] + (findDictWithKey(entry["data"], '@key', 'd' + str(BW_KEY_SCALE))["#text"]).lower()} for entry in dict_data["graphml"]["graph"]["edge"]]
    
    routerInfo = []
    edgeRouter = []
    for i in router:
        routerInfo.append({"routerID" : i["id"], "interface": []})
        for edge in link:
            if edge["source"] == i["id"]:
                routerInfo[i["id"]-1]["interface"].append(f'r{edge["source"]}-r{edge["target"]}')
            elif edge["target"] == i["id"]:
                routerInfo[i["id"]-1]["interface"].append(f'r{edge["target"]}-r{edge["source"]}')
            else:
                continue

        if len(routerInfo[i["id"]- 1]["interface"]) < 2:
            edgeRouter.append(routerInfo[i["id"]- 1])
    
    # print(edgeRouter)
    # print(findDictWithKey(edgeRouter, 'routerID', 6))
    return findDictWithKey(edgeRouter, 'routerID', 6)['interface'][0]

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if(self.path == '/log'):
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


class HTTPServerV6(HTTPServer):
    address_family = socket.AF_INET6

if __name__ == "__main__":
    #webServer = HTTPServer((hostName, serverPort), MyServer)
    # print(getIDSInterface())
    # cmd_list = f'sudo /usr/local/bin/snort -c /usr/local/etc/snort/snort.lua -s 65535 -k none -l /var/log/snort -i {getIDSInterface()} -m 0x1b'.split(" ")
    # subprocess.run(cmd_list)
    hostName = ip_route.get_addr()[1]["attrs"][0][1]
    webServer = HTTPServerV6((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass
    
    webServer.serve_close()
    print("Server stopped.")
