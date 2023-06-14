import socket
sock = socket.socket(socket.AF_INET6,socket.SOCK_STREAM)
sock.bind(('fd00:0:41::2', 9000))
sock.listen(1)

while True:
    print('wating for connection')
    connection, client_address = sock.accept()
    try:
        print('connected from', client_address)
        while True:
            data = connection.recv(16)
            print('received {!r}'.format(data))
            if data:
                print('sending data back to the client')
                connection.sendall(data)
            else:
                print('no data from', client_address)
                break
    finally:
        connection.close()
