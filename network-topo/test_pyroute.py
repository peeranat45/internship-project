from pyroute2 import IPRoute
ipr = IPRoute()
ipr.bind()
#print(ipr.get_links())
lists = [x.get_attr('IFLA_IFNAME') for x in ipr.get_links()]
print(lists)
# ipr.rule("add",table=250,priority=1000,src='fd00:0:11::2')
ipr.route("add", dst="fcff:1::100",oif=5,encap={"type":"seg6local","action":"End.DT6","table":250},)
# ipr.route("add",dst="fd00::/32", oif=2, encap={'type' : 'seg6', 'mode':'encap','segs': ["fcff:4::100","fd00:1:13::2"]},table=250)
#ipr.route("add", dst="2001:0:0:10::1/128", oif=2,encap={"type":"seg6", "mode":"encap","segs":"2005::9,2005::3,2000::6"}, table=110)

