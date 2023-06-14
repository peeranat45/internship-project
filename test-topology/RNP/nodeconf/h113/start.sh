#!/bin/sh
NODE_NAME=h113
GW_NAME=r11
IF_NAME=$NODE_NAME-$GW_NAME
IP_ADDR=fd00:0:113::2/64
GW_ADDR=fd00:0:113::1

ip -6 addr add $IP_ADDR dev $IF_NAME
ip -6 route add default via $GW_ADDR dev $IF_NAME
