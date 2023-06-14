import time 
from http.client import HTTPConnection
import json, sys, os
import argparse
from ipaddress import ip_address, IPv6Address

from dotenv import load_dotenv

load_dotenv()

BW_KEY = int(os.getenv('BW_KEY'))
NODE_NUM = int(os.getenv('HOST_NODE'))
BW_KEY_VALUE=int(os.getenv('BW_KEY_VALUE'))
BW_KEY_SCALE=os.getenv('BW_KEY_SCALE')
TOPO_FILE=str(os.getenv('TOPO_FILE'))
CON_ROUTER=str(os.getenv('CON_ROUTER'))
EGR_ROUTER=str(os.getenv('EGR_ROUTER'))
IDS_ADDR=str(os.getenv('IDS_ADDR'))
HOST_SOURCE=str(os.getenv('HOST_SOURCE'))
HOST_DST=str(os.getenv('HOST_DST'))
IDS_APP=str(os.getenv('IDS_APP'))
ING_ROUTER=str(os.getenv('ING_ROUTER'))


def validIPAddress(IP: str) -> str:
    try:
        return True if type(ip_address(IP)) is IPv6Address else False
    except ValueError:
        sys.exit("Invalid IP")

controllerName = CON_ROUTER
controllerPort = 8080

# parser = argparse.ArgumentParser(prog='Assgin Default')
# parser.add_argument('controllerAddress', type=str, help='Controller IPv6 Addresse ex. fcff:3::1')
# parser.add_argument('idsAddress', type=str, help='IDS Address ex. fcff:4::1')
# parser.add_argument('egressAddress', type=str, help="Egress router addres ex. fcff:10::100")

# args = parser.parse_args()

# validIPAddress(args.controllerAddress)
# validIPAddress(args.idsAddress)
# validIPAddress(args.egressAddress)
# controllerName = args.controllerAddress

paths = []
paths.append(EGR_ROUTER[:-1] + "100")
paths.append(IDS_ADDR)

headers = {"Content-type" : "application/json"}
paths_command = { "command" : [
       {
           "app" : "ids_app",
           "op" : "add",
           "segments" : paths
        },
        {
            "app" : "directly_route",
            "op" : "add",
            "segments" : [EGR_ROUTER[:-1] + "100"]
        }
    ]}

policy_command ={ "command" : [
        {
            "app" : "ids_app",
            "op" : "add",
            "src_addr" : "fd00::/32"
        }
    ]} 
con0 = HTTPConnection(controllerName, controllerPort, timeout=10)
con = HTTPConnection(controllerName, controllerPort, timeout=10)
con0.request('POST', "/paths",json.dumps(paths_command).encode(), headers)
con.request('POST', "/policy", json.dumps(policy_command).encode(), headers)
