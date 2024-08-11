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




def timeInServer(serverId,req_type, req_time):
    t = float(req_time)
    
    if req_type == 'P':
        if serverId == 3:
            return t * 2
        else:
            return t
    if req_type == 'M':
        if serverId == 3:
            return t
        else:
            return t * 2
    if req_type == 'V':
        if serverId == 3:
            return t * 3
        else:
            return t
            
    servPrint('recieved unknown request')
    sys.exit()



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
    t = float(req_time)
    if req_type == "V" or req_type == "P":
    #if there is a pressure on the servers 1 and 2 and the server 3 is in a better state give some of the request to it in some conditions
        if s2 > 10 and s1 > 10 and s3 < 15 :
            if req_type == "V" and (v3 == 0 or req_time < 4) 
                next_server = 3
                s3 += (t*3)
            else if req_type == "P" and (v3 == 0 or req_time < 5) 
                next_server = 3
                s3 += (t*2)
            else:
                if s2 >= s1:
                    next_server = 1
                    s1 += t

                else: 
                    next_server = 2
                    s2 += t
            lock.release()
            return next_server
        #normally we want the trafic to go to the servers designed for video 1 , 2             
        else:
            if s2 >= s1:
                next_server = 1
                s1 += t

            else: 
                next_server = 2
                s2 += t        
        lock.release()
        return next_server    
        
    else if req_type == "M":
        if s3 >= 15 and s2 <= 10 and s1 <= 10 and (s2 == 0 or s1 == 0 or req_time < 5) :
            if s2 >= s1:
                next_server = 1
                s1 += (t * 2)
            else:
                next_server = 2
                s2 += (t * 2)
            lock.release()
            return next_server 
         
        next_server = 3
        s3 += t
    lock.release()
    return next_server 


def parseRequest(req):
    return (
     req[0], req[1])


class LoadBalancerRequestHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        global s1
        global s2
        global s3
        global lock2
        lock2.acquire
        client_sock = self.request
        req = client_sock.recv(2)
        req_type, req_time = parseRequest(req)
        servID  = getNextServer(req_type, req_time)
        realTime = timeInServer(servID,req_type,req_time)
        LBPrint('recieved request %s from %s, sending to %s' % (req, self.client_address[0], getServerAddr(servID)))
        serv_sock = getServerSocket(servID)
        serv_sock.sendall(req)
        data = serv_sock.recv(2)
        if servID == 1:
            s1 -= realTime
        elif servID == 2:
            s2 -= realTime
        elif servID == 3:
            s3 -= realTime
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
