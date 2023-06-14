#!/bin/sh
NODE_NAME=h142
GW_NAME=r14
IF_NAME=$NODE_NAME-$GW_NAME
IP_ADDR=fd00:0:142::2/64
GW_ADDR=fd00:0:142::1

ip -6 addr add $IP_ADDR dev $IF_NAME
ip -6 route add default via $GW_ADDR dev $IF_NAME
