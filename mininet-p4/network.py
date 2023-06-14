import python_hosts
import os
import shutil
from mininet.node import Host, Switch
from mininet.cli import CLI
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel, info, error, debug
from mininet.net import Mininet
from mininet.moduledeps import pathCheck


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

class P4Switch(Switch):

    device_id = 0
    def __init__(self, name, sw_path = None, json_path = None, thrift_port = None, pcap_dump = False, log_console = False, verbose = False, device_id = None, enable_debugger = False, **kwargs):
        Switch.__init__(self, name, **kwargs)
        assert(sw_path)
        assert(json_path)
        # make sure that the provided sw_path is valid
        pathCheck(sw_path)
        # make sure that the provided JSON file exists
        if not os.path.isfile(json_path):
            error("Invalid JSON file.\n")
        self.sw_path = sw_path
        self.json_path = json_path
        self.verbose = verbose
        logfile = "/tmp/p4s.{}.log".format(self.name)
        self.output = open(logfile, 'w')
        self.thrift_port = thrift_port
        self.pcap_dump = pcap_dump
        self.enable_debugger = enable_debugger
        self.log_console = log_console
        if device_id is not None:
            self.device_id = device_id
            P4Switch.device_id = max(P4Switch.device_id, device_id)
        else:
            self.device_id = P4Switch.device_id
            P4Switch.device_id += 1
        self.nanomsg = "ipc:///tmp/bm-{}-log.ipc".format(self.device_id)


        @classmethod
        def setup(cls):
            pass

        def check_switch_started(self, pid):
            """While the process is running (pid exists), we check if the Thrift
            server has been started. If the Thrift server is ready, we assume that
            the switch was started successfully. This is only reliable if the Thrift
            server is started at the end of the init process"""
            while True:
                if not os.path.exists(os.path.join("/proc", str(pid))):
                    return False
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    sock.settimeout(0.5)
                    result = sock.connect_ex(("localhost", self.thrift_port))
                finally:
                    sock.close()
                if result == 0:
                    return  True

        def start(self, controllers):
            "Start up a new P4 switch"
            info("Starting P4 switch {}.\n".format(self.name))
            args = [self.sw_path]
            for port, intf in self.intfs.items():
                if not intf.IP():
                    args.extend(['-i', str(port) + "@" + intf.name])
            if self.pcap_dump:
                args.append("--pcap")
                # args.append("--useFiles")
            if self.thrift_port:
                args.extend(['--thrift-port', str(self.thrift_port)])
            if self.nanomsg:
                args.extend(['--nanolog', self.nanomsg])
            args.extend(['--device-id', str(self.device_id)])
            P4Switch.device_id += 1
            args.append(self.json_path)
            if self.enable_debugger:
                args.append("--debugger")
            if self.log_console:
                args.append("--log-console")
            logfile = "/tmp/p4s.{}.log".format(self.name)
            info(' '.join(args) + "\n")

            pid = None
            with tempfile.NamedTemporaryFile() as f:
                # self.cmd(' '.join(args) + ' > /dev/null 2>&1 &')
                self.cmd(' '.join(args) + ' >' + logfile + ' 2>&1 & echo $! >> ' + f.name)
                pid = int(f.read())
            debug("P4 switch {} PID is {}.\n".format(self.name, pid))
            if not self.check_switch_started(pid):
                error("P4 switch {} did not start correctly.\n".format(self.name))
                exit(1)
            info("P4 switch {} has been started.\n".format(self.name))

        def stop(self):
            "Terminate P4 switch."
            self.output.flush()
            self.cmd('kill %' + self.sw_path)
            self.cmd('wait')
            self.deleteIntfs()

        def attach(self, intf):
            "Connect a data port"
            assert(0)

        def detach(self, intf):
            "Disconnect a data port"
            assert(0)
    


# Define a function

def add_link(my_net, node1, node2):
    my_net.addLink(node1, node2, intfName1=node1.name + '-' + node2.name, intfName2=node2.name+'-'+node1.name)
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
    h11 = net.addHost('h11', cls=BaseNode)
    h41 = net.addHost('h41', cls=BaseNode)

    # Switchs
    s1 = net.addHost('s1', cls=BaseNode)

    # Routers
    r1 = net.addHost('r1', cls=Router)
    r2 = net.addHost('r2', cls=Router)
    r3 = net.addHost('r3', cls=Router)
    r4 = net.addHost('r4', cls=Router)

    # Switchs
    # s1 = net.addSwitch('s1', cls=P4Switch, sw_path="../../lib/behavioral-model/targets/simple_switch/simple_switch", json_path="./main.json")
    # s1 = net.addSwitch('s1', cls=P4Switch, sw_path="../../lib/behavioral-model/targets/simple_switch/simple_switch", json_path="./main.json")
    # Links
    add_link(net, h11, r1)
    add_link(net, h41, r4)

    add_link(net, r1, s1)
    add_link(net, s1, r2)
    add_link(net, r2, r3)
    add_link(net, r2, r4)
    add_link(net, r3, r4)


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



