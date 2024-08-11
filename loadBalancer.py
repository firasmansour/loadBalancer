import socket, SocketServer, Queue, sys, time, threading
HTTP_PORT = 80
previous_server = 3
s1 = 0
s2 = 0
s3 = 0

lock = threading.Lock()
lock2 = threading.Lock()

SERV_HOST = '10.0.0.1'
servers = {'serv1': ('192.168.0.101', None), 'serv2': ('192.168.0.102', None), 'serv3': ('192.168.0.103', None)}

def LBPrint(string):
    print '%s : %s-----' % (time.strftime('%H:%M:%S', time.localtime(time.time())), string)








def createSocket(addr, port):
    for res in socket.getaddrinfo(addr, port, socket.AF_UNSPEC, socket.SOCK_STREAM):
        af, socktype, proto, canonname, sa = res
        try:
            new_sock = socket.socket(af, socktype, proto)
        except socket.error as msg:
            LBPrint(msg)
            new_sock = None
            continue

        try:
            new_sock.connect(sa)
        except socket.error as msg:
            LBPrint(msg)
            new_sock.close()
            new_sock = None
            continue

        break

    if new_sock is None:
        LBPrint('could not open socket')
        sys.exit(1)
    return new_sock


def getServerSocket(servID):
    name = 'serv%d' % servID
    return servers[name][1]


def getServerAddr(servID):
    name = 'serv%d' % servID
    return servers[name][0]


def getNextServer(req_type, req_time):
    global lock
    global previous_server
    global s1
    global s2
    global s3
    lock.acquire()
    if req_type == "V" or req_type == "P":
        if previous_server == 1:
            next_server = 2
            s2 += (int)req_time
        elif previous_server == 2 :
            next_server = 1
            s1 += (int)req_time
        else: 
            next_server = 1
            s1 += (int)req_time
    else:
        if s3 >= 20:
            if s2 >= s1:
                next_server = 1
                s1 += ((int)req_time * 2)
            else:
                next_server = 2
                s2 += ((int)req_time * 2)
        else: 
            next_server = 3
            s3 += (int)req_time
    previous_server = next_server
    lock.release()
    return next_server


def parseRequest(req):
    return (
     req[0], req[1])


class LoadBalancerRequestHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        global lock2
        lock2.acquire
        client_sock = self.request
        req = client_sock.recv(2)
        req_type, req_time = parseRequest(req)
        servID = getNextServer(req_type, req_time)
        LBPrint('recieved request %s from %s, sending to %s' % (req, self.client_address[0], getServerAddr(servID)))
        serv_sock = getServerSocket(servID)
        serv_sock.sendall(req)
        data = serv_sock.recv(2)
        
        client_sock.sendall(data)
        client_sock.close()
        lock2.release


class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass


if __name__ == '__main__':
    try:
        LBPrint('LB Started')
        LBPrint('Connecting to servers')
        for name, (addr, sock) in servers.iteritems():
            servers[name] = (
             addr, createSocket(addr, HTTP_PORT))

        server = ThreadedTCPServer((SERV_HOST, HTTP_PORT), LoadBalancerRequestHandler)
        server.serve_forever()
    except socket.error as msg:
        LBPrint(msg)

# okay decompiling exampleLB.pyc
