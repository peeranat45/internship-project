import json, xmltodict, os
from dotenv import load_dotenv

load_dotenv()

BW_KEY = int(os.getenv('BW_KEY'))
NODE_NUM = int(os.getenv('HOST_NODE'))
BW_KEY_VALUE=int(os.getenv('BW_KEY_VALUE'))
BW_KEY_SCALE=os.getenv('BW_KEY_SCALE')
TOPO_FILE=str(os.getenv('TOPO_FILE'))

with open(TOPO_FILE) as xml_file:
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

# Preparing data"
router = [{"id" : int(entry["@id"]) + 1, "name" : entry["data"][-1]["#text"]} for entry in dict_data["graphml"]["graph"]["node"]] 
link = [{"source": int(entry["@source"]) + 1, "target": int(entry["@target"]) + 1, "bw" : findDictWithKey(entry["data"], '@key', 'd' + str(BW_KEY_VALUE))["#text"] + (findDictWithKey(entry["data"], '@key', 'd' + str(BW_KEY_SCALE))["#text"]).lower()} for entry in dict_data["graphml"]["graph"]["edge"]]
print(link)
# print(router)


# Create nodeconf folder
BASEDIR = os.getcwd()
if not os.path.exists(BASEDIR + "/nodeconf/"):
    os.mkdir("nodeconf")

# Create zebra.conf file
for i in router:
    if not os.path.exists(BASEDIR + "/nodeconf/r" + str(i["id"])):
        os.mkdir("nodeconf/r" + str(i["id"]))
    #Check zebra.sh file
    if not os.path.exists(BASEDIR + "/nodeconf/r" + str(i["id"]) + "/zebra.conf"):
        zebraFile = open(BASEDIR + "/nodeconf/r" + str(i["id"]) + "/zebra.conf", "w")
        zebra = f'!\nhostname r{i["id"]}\n!\ndebug zebra events\ndebug zebra rib\n!\n'
        # print(zebra)
    # break
    else:
        continue
    
    for hostID in range(1, NODE_NUM+1):
        zebra += f'interface r{i["id"]}-h{i["id"]}{hostID}\n'
        zebra += f' ipv6 address fd00:0:{i["id"]}{hostID}::1/64\n!\n'

    for edge in link:
        if edge["source"] == i["id"]:
            zebra += f'interface r{edge["source"]}-r{edge["target"]}\n'
        elif edge["target"] == i["id"]:
            zebra += f'interface r{edge["target"]}-r{edge["source"]}\n'
        else:
            continue
        zebra += f' ipv6 address fcf0:0:{min(edge["source"],edge["target"])}:{max(edge["source"],edge["target"])}::'
        if edge["source"] == i["id"]:
            zebra += f'{1 if edge["source"] < edge["target"] else 2}/64\n!\n'
        elif edge["target"] == i["id"]:
            zebra += f'{1 if edge["target"] < edge["source"] else 2}/64\n!\n'

    
    zebra += f'interface lo\n ipv6 address fcff:{i["id"]}::1/32\n!\nipv6 forwarding\n!\nline vty\n!\n'
    # print(zebra)
    zebraFile.write(zebra)
    zebraFile.close()

# Create ospf6d.conf file
for i in router:
    if not os.path.exists(BASEDIR + "/nodeconf/r" + str(i["id"]) + "/ospf6d.conf"):
        ospf6dFile = open(BASEDIR + "/nodeconf/r" + str(i["id"]) + "/ospf6d.conf", "w")
        ospf6d = f'hostname r{i["id"]}\ndebug ospf6 message all\ndebug ospf6 lsa unknown\ndebug ospf6 zebra\ndebug ospf6 interface\ndebug ospf6 neighbor\ndebug ospf6 route table\ndebug ospf6 flooding\n!\n'
    else:
        continue
    for edge in link:
        if edge["source"] == i["id"]:
            ospf6d += f'interface r{edge["source"]}-r{edge["target"]}\n ipv6 ospf6 network broadcast\n!\n'
        elif edge["target"] == i["id"]:
            ospf6d += f'interface r{edge["target"]}-r{edge["source"]}\n ipv6 ospf6 network broadcast\n!\n'
        else:
            continue
    
    ospf6d += f'router ospf6\n ospf6 router-id 10.0.0.{i["id"]}\n log-adjacency-changes detail\n redistribute connected\n'
    for edge in link:
        if edge["source"] == i["id"]:
            ospf6d += f' interface r{edge["source"]}-r{edge["target"]} area 0.0.0.0\n'
        elif edge["target"] == i["id"]:
            ospf6d += f' interface r{edge["target"]}-r{edge["source"]} area 0.0.0.0\n'
    for hostID in range(1, NODE_NUM+1):
        ospf6d += f' interface r{i["id"]}-h{i["id"]}{hostID} area 0.0.0.0\n'
    ospf6d += f' passive-interface default\n!\n'
    ospf6dFile.write(ospf6d)
    ospf6dFile.close()
    # break

# Add SRv6 function to edge router
# With only one connection between router
"""
    {
        "routerID" : int,
        "interface" : ["r1-r2",]
    }
"""
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

# print(routerInfo)
print(edgeRouter)
for i in edgeRouter:
    if not os.path.exists(BASEDIR + "/nodeconf/r" + str(i["routerID"]) + "/iproute.sh"):
         iprouteFile = open(BASEDIR + "/nodeconf/r" + str(i["routerID"]) + "/iproute.sh", "w")
    else:
        continue

    iproute = f'ip -6 route add fcff:{i["routerID"]}::100 encap seg6local action End.DT6 table main dev {i["interface"][0]}'
    iprouteFile.write(iproute)
    iprouteFile.close()




# Create start.sh
for i in router:
    if not os.path.exists(BASEDIR + "/nodeconf/r" + str(i["id"]) + "/start.sh"):
         startFile = open(BASEDIR + "/nodeconf/r" + str(i["id"]) + "/start.sh", "w")
    else:
        continue
    start = f'#/bin/sh\nBASE_DIR=nodeconf\nNODE_NAME=r{i["id"]}\nFRR_PATH=/usr/lib/frr\n'

    #enable IPv6 forwarding
    start += f'sysctl -w net.ipv6.conf.all.forwarding=1\necho "no service integrated-vtysh-config" >> /etc/frr/vtysh.conf\nchown frr:frr $BASE_DIR/$NODE_NAME\n'
    start += f'$FRR_PATH/zebra -f "$PWD"/$BASE_DIR/$NODE_NAME/zebra.conf -d -z "$PWD"/$BASE_DIR/$NODE_NAME/zebra.sock -i "$PWD"/$BASE_DIR/$NODE_NAME/zebra.pid\n'
    start += f'$FRR_PATH/ospf6d -f "$PWD"/$BASE_DIR/$NODE_NAME/ospf6d.conf -d -z "$PWD"/$BASE_DIR/$NODE_NAME/zebra.sock -i "$PWD"/$BASE_DIR/$NODE_NAME/ospf6d.pid\n'

    #enable segment routing for ipv6
    start += "sysctl -w net.ipv6.conf.all.seg6_enabled=1\nfor dev in $(ip -o -6 a | awk '{ print $2 }' | grep -v \"lo\")\ndo\n\tsysctl -w net.ipv6.conf.\"$dev\".seg6_enabled=1\ndone\n"
    for j in edgeRouter:
        if j['routerID'] == i["id"]:
            start += f'bash "$PWD"/$BASE_DIR/$NODE_NAME/iproute.sh\n'
    print(edgeRouter)
    startFile.write(start)
    startFile.close()



# Create etc_hosts file
def isEdgeRouter(routerID, edgeRouter):
    for i in edgeRouter:
        if i["routerID"] ==  routerID:
           return True
    return False

if not os.path.exists(BASEDIR + "/etc-hosts"):
    etc_hostsFile = open(BASEDIR + "/etc-hosts", "w")
    etc_hosts = f'# Mininet hosts\n\n# Routers\n'
    etc_host_hosts = ''
    for i in router:
        etc_hosts += f'fcff:{i["id"]}::1\tr{i["id"]}\n'
        if isEdgeRouter(i["id"], edgeRouter):
            for hostID in range(1, NODE_NUM+ 1):
                etc_host_hosts += f'fd00:0:{i["id"]}{hostID}::2\th{i["id"]}{hostID}\n'
    etc_hostsFile.write(etc_hosts)
    etc_hostsFile.write('\n# Hosts\n')
    etc_hostsFile.write(etc_host_hosts)
    etc_hostsFile.close()

# Create host at edge node
for router in edgeRouter:
    for hostID in range(1,NODE_NUM + 1):
        if not os.path.exists(BASEDIR + f'/nodeconf/h{router["routerID"]}' + str(hostID)):
            os.mkdir(f'nodeconf/h{router["routerID"]}' + str(hostID))
        #Check zebra.sh file"
        if not os.path.exists(BASEDIR + f'/nodeconf/h{router["routerID"]}' + str(hostID) + "/start.sh"):
            startFile = open(BASEDIR + f'/nodeconf/h{router["routerID"]}' + str(hostID) + "/start.sh", "w")
            start = ''
        else:
            continue
        start += f'#!/bin/sh\n'
        start += f'NODE_NAME=h{router["routerID"]}{hostID}\n'
        start += f'GW_NAME=r{router["routerID"]}\n'
        start += f'IF_NAME=$NODE_NAME-$GW_NAME\n'
        start += f'IP_ADDR=fd00:0:{router["routerID"]}{hostID}::2/64\n'
        start += f'GW_ADDR=fd00:0:{router["routerID"]}{hostID}::1\n\n'
        start += f'ip -6 addr add $IP_ADDR dev $IF_NAME\n'
        start += f'ip -6 route add default via $GW_ADDR dev $IF_NAME\n'
        startFile.write(start)
        startFile.close()




