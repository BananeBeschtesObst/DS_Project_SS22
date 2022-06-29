import socket


BROADCAST_PORT=10001



def get_ip():
    hostname=socket.gethostname()
    ip_address=socket.gethostbyname(hostname)
    return ip_address

def unicast_TCP_listener():
    s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    addr=(get_ip(),0)
    s.bind(addr)
    s.listen()
    return s

def unicast_TCP_sender(msg, addr):
    transmit_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transmit_socket.settimeout(1)
    transmit_socket.connect(addr)
    transmit_socket.send(msg)
    transmit_socket.close()

def broadcast_UDP_listener():
    s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    addr=(get_ip(),10001)
    s.bind(addr)
    return s

def broadcast_UDP_sender(timeout=None):
    s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    addr=(get_ip(), 0)
    s.bind(addr)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    if timeout:
        s.settimeout(timeout)
    return s

def multicast_UDP_listener():
    s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    addr=(get_ip(), 0)
    s.bind(addr)
    return s

def multicast_UDP_sender():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0.2)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
    return s

def create_node (request_type, requester_type, addr):
    return {'Request_Type': request_type, 'requester_type': requester_type, 'Address': addr}    #request type e.g. "Join"; requester_type e.g. Server; Adress = Server or Client Adress

def create_msg_node (msg_type, msg, addr):
    return {'Message_Type': msg_type,'Message': msg, 'Address': addr}