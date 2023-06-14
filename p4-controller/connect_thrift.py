import sys

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.protocol import TMultiplexedProtocol

def a(ip, port, services, out=sys.stdout):
    
    transport = TSocket.TSocket(ip, port)

    transport = TTransport.TBufferedTransport(transport)

    bprotocol = TBinaryProtocol.TBinaryProtocol(transport)

    clients = []

    transport.open()

a("0.0.0.0", 9090,"")
