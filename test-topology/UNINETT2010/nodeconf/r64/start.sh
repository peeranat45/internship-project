#/bin/sh
BASE_DIR=nodeconf
NODE_NAME=r64
FRR_PATH=/usr/lib/frr
sysctl -w net.ipv6.conf.all.forwarding=1
echo "no service integrated-vtysh-config" >> /etc/frr/vtysh.conf
chown frr:frr $BASE_DIR/$NODE_NAME
$FRR_PATH/zebra -f "$PWD"/$BASE_DIR/$NODE_NAME/zebra.conf -d -z "$PWD"/$BASE_DIR/$NODE_NAME/zebra.sock -i "$PWD"/$BASE_DIR/$NODE_NAME/zebra.pid
$FRR_PATH/ospf6d -f "$PWD"/$BASE_DIR/$NODE_NAME/ospf6d.conf -d -z "$PWD"/$BASE_DIR/$NODE_NAME/zebra.sock -i "$PWD"/$BASE_DIR/$NODE_NAME/ospf6d.pid
sysctl -w net.ipv6.conf.all.seg6_enabled=1
for dev in $(ip -o -6 a | awk '{ print $2 }' | grep -v "lo")
do
	sysctl -w net.ipv6.conf."$dev".seg6_enabled=1
done
bash "$PWD"/$BASE_DIR/$NODE_NAME/iproute.sh
