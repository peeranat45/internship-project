
# First pair: veth0-veth1
#sudo ip link add name veth0 type veth peer name veth1
#sudo ip link set dev veth0 up
#sudo ip link set dev veth1 up
#sudo ip link set veth0 mtu 9500
#sudo ip link set veth1 mtu 9500
#sudo sysctl net.ipv6.conf.veth0.disable_ipv6=1
#sudo sysctl net.ipv6.conf.veth1.disable_ipv6=1

# Second pair: veth2-veth3
#sudo ip link add name veth2 type veth peer name veth3
#sudo ip link set dev veth2 up
#sudo ip link set dev veth3 up
#sudo ip link set veth2 mtu 9500
#sudo ip link set veth3 mtu 9500
#sudo sysctl net.ipv6.conf.veth2.disable_ipv6=1
#sudo sysctl net.ipv6.conf.veth3.disable_ipv6=1

#sudo simple_switch --interface 0@veth0 --interface 1@veth2 main.bmv2/main.json &



