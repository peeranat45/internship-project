import time 
from http.client import HTTPConnection
import json

controllerName = 'fcff:4::1'
controllerPort = '8080'

print("Sending Request....")
command =  {
    "command" : [
    {
        "app" : "ids_app",
        "op" : "add",
        "src_addr" : "fd00:0:14::2"
    }
    ]
    }
con = HTTPConnection(controllerName,controllerPort,timeout=10)
headers = {"Content-type" : 'application/json'}
con.request('POST', '/', json.dumps(command).encode(), headers)
response = con.getresponse()
print(response.read().decode())

