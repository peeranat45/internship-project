import python_hosts
import os
import shutil
from mininet.node import Host, Switch
from mininet.cli import CLI
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel, info, error, debug
from mininet.net import Mininet
from mininet.moduledeps import pathCheck

import json, xmltodict
from dotenv import load_dotenv

load_dotenv()
# Get value from .env
BW_KEY = int(os.getenv('BW_KEY'))
HOST_NODE = int(os.getenv('HOST_NODE'))
BW_KEY_VALUE=int(os.getenv('BW_KEY_VALUE'))
BW_KEY_SCALE=os.getenv('BW_KEY_SCALE')
TOPO_FILE=str(os.getenv('TOPO_FILE'))
CON_ROUTER=str(os.getenv('CON_ROUTER'))

# from p4utils.mininetlib.network_API import NetworkAPI

# const variable
FRR_BIN = "/usr/lib/frr"
BASEDIR = os.getcwd() + "/nodeconf/"
OUTPUT_PID_TABLE_FILE = "/tmp/pid_table_file.txt"
PRIVDIR = '/var/priv'

ETC_HOSTS_FILE = './etc-hosts'




# Define new Class
class BaseNode(Host):
    def __init__(self, name, *args, **kwargs):
        dirs = [PRIVDIR, '/var/run/frr']
        # dirs = [PRIVDIR]
        Host.__init__(self, name, privateDirs=dirs, *args, **kwargs)
        self.dir = "/tmp/%s" % name
        self.nets = []
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)
    
    def config(self, **kwargs):
        # Remove any configured address

        Host.config(self, **kwargs)

        for intf in self.intfs.values():
            self.cmd('ifconfig %s 0' % intf.name)
        
        self.cmd("echo '" + self.name + "' > " + PRIVDIR + "/hostname")
        if os.path.isfile(BASEDIR + self.name + "/start.sh"):
            print('source %s' % BASEDIR + self.name + "/start.sh")
            self.cmd('source %s' % BASEDIR + self.name + "/start.sh")
    
    def cleanup(self):
        def remove_if_exists(filename):
            if os.path.exists(filename):
                os.remove(filename)
        
        Host.cleanup(self)

        if os.path.exists(self.dir):
            shutil.rmtree(self.dir)
        
        remove_if_exists(BASEDIR + self.name + "/zebra.pid")
        remove_if_exists(BASEDIR + self.name + "/zebra.log")
        remove_if_exists(BASEDIR + self.name + "/zebra.sock")
        remove_if_exists(BASEDIR + self.name + "/ospf6d.pid")
        remove_if_exists(BASEDIR + self.name + "/ospf6d.log")
        remove_if_exists(BASEDIR + self.name + "/ospf6d.log")
        remove_if_exists(BASEDIR + self.name + "/ospf6d.pid")

        remove_if_exists(OUTPUT_PID_TABLE_FILE)

class Router(BaseNode):
    def __init__(self, name, *args, **kwargs):
        BaseNode.__init__(self, name, *args, **kwargs)


# Define a function

def add_link(my_net, node1, node2, bw=None, delay='10ms', jitter=None, loss=None):
    my_net.addLink(node1, node2, intfName1=node1.name + '-' + node2.name, intfName2=node2.name+'-'+node1.name, delay=delay,bw=bw, jitter=jitter, loss=loss)
    # my_net.addLink(node1, node2, intfName1=node1 + '-' + node2, intfName2=node2+'-'+node1)

def add_nodes_to_etc_hosts():
    # Get /etc/hosts
    etc_hosts = python_hosts.hosts.Hosts()

    count = etc_hosts.import_file(ETC_HOSTS_FILE)

    count =  count['add_result']['ipv6_count'] + count['add_result']['ipv4_count']
    print('*** Added %s entries to /etc/hosts\n' % count)

def remove_nodes_from_etc_hosts(net):
    print('*** Removing entries from /etc/hosts\n')

    etc_hosts = python_hosts.hosts.Hosts()
    for host in net.hosts:
        etc_hosts.remove_all_matching(name=str(host))
    
    etc_hosts.write()

def stop_all():
    os.system('sudo mn -c')

def extract_host_pid(dumpline):
    temp = dumpline[dumpline.find('pid=') + 4:]
    return int(temp[:len(temp) - 2])


def _main():
    net = Mininet(topo=None, build=False, controller=None)



    # Network general options
    setLogLevel('info')


    # Network definition

    # Hosts
    # h11 = net.addHost('h11', cls=BaseNode)
    
    bw_key = 35

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

    routerList = []
    hostList = []
    for i in router:
        tempRouter = net.addHost(f'r{i["id"]}',cls=Router)
        routerList.append(tempRouter)
        # tempRouter.cmdPrint('ip -6 route show')
        if tempRouter.name == f'r{CON_ROUTER[-4]}':
            print(f"Controller Node = {tempRouter.name}")
            # tempRouter.cmdPrint(f'sudo python3 ./program/controller.py')
        if isEdgeRouter(i["id"], edgeRouter):
            # tempRouter.cmdPrint(f'sudo python3 ./program/router.py')
            for j in range(1, HOST_NODE+1):
                tempHost = net.addHost(f'h{i["id"]}{j}',cls=BaseNode)
                hostList.append(tempHost)
                add_link(net,tempHost, tempRouter)

    
    for i in link:
        temp_1 = None
        temp_2 = None
        for j in routerList:
            print(j.name)
            if j.name == "r"+str(i['source']):
                temp_1 = j
        for j in routerList:
            if j.name == "r"+str(i['target']):
                temp_2 = j
        add_link(net,temp_1, temp_2, bw=i["bw"])
    # Routers
    # r1 = net.addHost('r1', cls=Router)
    # r2 = net.addHost('r2', cls=Router)
    # r3 = net.addHost('r3', cls=Router)
    # r4 = net.addHost('r4', cls=Router)
    # r5 = net.addHost('r5', cls=Router)
    # r6 = net.addHost('r6', cls=Router)
    # r7 = net.addHost('r7', cls=Router)
    # r8 = net.addHost('r8', cls=Router)
    # r9 = net.addHost('r9', cls=Router)
    # r10 = net.addHost('r10', cls=Router)
    # r11 = net.addHost('r11', cls=Router)
    # r12 = net.addHost('r12', cls=Router)
    # r13 = net.addHost('r13', cls=Router)
    # r14 = net.addHost('r14', cls=Router)
    # r15 = net.addHost('r15', cls=Router)
    # r16 = net.addHost('r16', cls=Router)
    # r17 = net.addHost('r17', cls=Router)
    # r18 = net.addHost('r18', cls=Router)
    # r19 = net.addHost('r19', cls=Router)
    # r20 = net.addHost('r20', cls=Router)
    # r21 = net.addHost('r21', cls=Router)
    # r22 = net.addHost('r22', cls=Router)
    # r23 = net.addHost('r23', cls=Router)

    
    # add_link(r1, r2, bw='2.5g')
    # add_link(r1, r6, bw='2.5g')
    # add_link(r2, r20, bw='2.5g')
    # add_link(r2, r5, bw='2.5g')
    # add_link(r2, r7, bw='2.5g')
    # add_link(r1, r2, bw='2.5g')
    # add_link(r1, r2, bw='2.5g')
    # add_link(r1, r2, bw='2.5g')

    # # Links general options
    # net.setBwAll(5)

    # # Nodes general options
    # net.enablePcapDumpAll()
    # net.enableLogAll()

    # Start the network
    net.build()
    net.start()
    # net.startNetwork
    print("Dumping connection")
    dumpNodeConnections(net.hosts)

    with open(OUTPUT_PID_TABLE_FILE, "w") as file:
        for host in net.hosts:
            file.write("%s %d\n" % (host, extract_host_pid(repr(host))))
    
    add_nodes_to_etc_hosts()

    print("Hello")
    CLI(net)
    net.stop()
    stop_all()

    remove_nodes_from_etc_hosts(net)

if __name__ == '__main__':
    _main()



