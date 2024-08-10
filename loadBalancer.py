import socket
import SocketServer
import Queue
import sys
import time
import threading

HTTP_PORT = 80
previous_server = 3
lock = threading.Lock()
SERV_HOST = '10.0.0.1'
servers = {'serv1': ('192.168.0.101', None), 'serv2': ('192.168.0.102', None), 'serv3': ('192.168.0.103', None)}

# Define a queue to store incoming requests
request_queue = Queue.Queue()

def LBPrint(string):
    print('%s: %s-----' % (time.strftime('%H:%M:%S', time.localtime(time.time())), string))

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

def getNextServer():
    global lock
    global previous_server
    lock.acquire()
    next_server = previous_server % 3 + 1
    previous_server = next_server
    lock.release()
    return next_server

def parseRequest(req):
    return req[0], req[1]

def processQueue():
    while True:
        client_sock = request_queue.get()
        try:
            req = client_sock.recv(2)
            req_type, req_time = parseRequest(req)
            servID = getNextServer()
            LBPrint('received request %s from %s, sending to %s' % (req, client_sock.getpeername()[0], getServerAddr(servID)))
            serv_sock = getServerSocket(servID)
            serv_sock.sendall(req)
            data = serv_sock.recv(2)
            client_sock.sendall(data)
        except Exception as e:
            LBPrint(f'Error processing request: {e}')
            client_sock.sendall(b'Error')
        finally:
            client_sock.close()

class LoadBalancerRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        client_sock = self.request
        # Add the request to the queue
        request_queue.put(client_sock)

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

if __name__ == '__main__':
    try:
        LBPrint('LB Started')
        LBPrint('Connecting to servers')
        for name, (addr, sock) in servers.items():
            servers[name] = (addr, createSocket(addr, HTTP_PORT))

        server = ThreadedTCPServer((SERV_HOST, HTTP_PORT), LoadBalancerRequestHandler)
        
        # Start a thread to process requests from the queue
        queue_processor_thread = threading.Thread(target=processQueue)
        queue_processor_thread.daemon = True
        queue_processor_thread.start()
        
        server.serve_forever()
    except socket.error as msg:
        LBPrint(msg)
