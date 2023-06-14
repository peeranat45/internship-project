import time 
from http.client import HTTPConnection
import json, os
from dotenv import load_dotenv

load_dotenv()
CON_ROUTER=str(os.getenv('CON_ROUTER'))
EGR_ROUTER=str(os.getenv('EGR_ROUTER'))
IDS_ADDR=str(os.getenv('IDS_ADDR'))
HOST_SOURCE=str(os.getenv('HOST_SOURCE'))
HOST_DST=str(os.getenv('HOST_DST'))
IDS_APP=str(os.getenv('IDS_APP'))
ING_ROUTER=str(os.getenv('ING_ROUTER'))

controllerName = CON_ROUTER
controllerPort = '8080'

idsServerName = IDS_ADDR
idsServerPort = 8080

#idsServerName = 'localhost'
#idsServerPort = 9000

#controllerName = 'localhost'
#controllerPort = 8080

timeout = 2 # Minute

paths = ["fcff:4::100","fcff:5::1"]

"""
{
    "command" : [
        {
            "app" : "ids_app",
            "op" : "add" | "del",
            "src_addr" : "fd00:0:14::2/128"
        }
    ]
}
"""

def check_value_in_list_of_dicts(lst, key, value):
    for dictionary in lst:
        if key in dictionary and dictionary[key] == value:
            return True
    return False

if __name__ == "__main__":
    # headers = {"Content-type" : "application/json"}
    # paths_command = { "command" : [
    #    {
    #        "app" : "ids_app",
    #        "op" : "add",
    #        "segments" : paths
    #     },
    #     {
    #         "app" : "directly_route",
    #         "op" : "add",
    #         "segments" : ["fcff:4::100"]
    #     }
    # ]}

    # policy_command ={ "command" : [
    #     {
    #         "app" : "ids_app",
    #         "op" : "add",
    #         "src_addr" : "fd00::/32"
    #     }
    # ]} 
    # con0 = HTTPConnection(controllerName, controllerPort, timeout=10)
    # con = HTTPConnection(controllerName, controllerPort, timeout=10)
    # con0.request('POST', "/paths",json.dumps(paths_command).encode(), headers)
    # con.request('POST', "/policy", json.dumps(policy_command).encode(), headers)

    while True:
        con1 = HTTPConnection(idsServerName,idsServerPort, timeout=10)
        con2 = HTTPConnection(controllerName, controllerPort, timeout=10)
        headers = {"Content-type" : "application/json"}
        con1.request('GET', '/log')
        con2.request('GET', '/rules')
        res_ids_list = json.loads(con1.getresponse().read().decode())
        # print(res_ids_list)
        # time.sleep(1)
        res_router_rules = json.loads(con2.getresponse().read().decode())["data"]
        commands = []
        print(res_router_rules)
        for data in res_ids_list:
            # Packet get IDS within last 10 minute
            if data["time_seconds"] < timeout * 60:
                # add rules if rules not exist
                print(data["src_addr"])
                print(data["time_seconds"])
                if not check_value_in_list_of_dicts(res_router_rules, "addr", data["src_addr"]):
                    commands.append({
                        "app" : "directly_route",
                        "op" : "add",
                        "src_addr" : data["src_addr"]
                    })
            elif data["time_seconds"] >= timeout * 60:
                # print(data["src_addr"])
                if check_value_in_list_of_dicts(res_router_rules, "addr", data["src_addr"]):
                    commands.append({
                        "app" : "directly_route",
                        "op" : "del",
                        "src_addr" : data["src_addr"]
                    })
        print(commands)
        con3 = HTTPConnection(controllerName,controllerPort, timeout=10)
        headers = {"Content-type" : 'application/json'}
        con3.request('POST', '/policy', json.dumps({"command" : commands}).encode(), headers)
        response = con3.getresponse()
        print(response.read().decode())
        # print(res_router_rules)
        # for rule in res_router_rules:


        time.sleep(1)

# Testing
# print("Sending Request....")
# command =  {
#     "command" : [
#     {
#         "app" : "ids_app",
#         "op" : "add",
#         "src_addr" : "fd00:0:14::2"
#     }
#     ]
#     }
# con = HTTPConnection(controllerName,controllerPort,timeout=10)
# headers = {"Content-type" : 'application/json'}
# con.request('POST', '/', json.dumps(command).encode(), headers)
# response = con.getresponse()
# print(response.read().decode())

