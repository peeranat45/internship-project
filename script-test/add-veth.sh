sudo modprobe dummy
sudo ip link add veth0 type dummy
ip link set veth0 up
ip addr add fcff:3::200/32 dev veth0

