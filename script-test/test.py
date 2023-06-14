from pyroute2 import IPRoute
import socket

ipr = IPRoute()
# ipr.rule('add', table=10, priority=32000,  src='fd00::/32')
# print(ipr.get_rules(family=socket.AF_INET6)[2])
# ipr.rule("add", table=250, priority=1,src="fcff:1::1")
# ls = ipr.get_routes(table=250,family=socket.AF_INET6)
# print(ls[0])
print([x.get_attr('IFLA_IFNAME') for x in ipr.get_links()])
# ls = [{
#     "src_len" : x['src_len'],
#     "dst_len" : x['dst_len'],
#     "table" : x['table'],
#     "attr" : x["attrs"]
# } for x in ipr.get_rules(family=socket.AF_INET6)]

# print(ls)
# print(ipr.get_routes(family=socket.AF_INET6, table=255))
