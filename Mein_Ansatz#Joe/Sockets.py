import socket
import struct
import threading

SERVER_LIST=[]
LEADER=''
BROADCAST_CODE_CLIENT='Nicetomeetyou'
CLIENT_LIST=[]
CLIENT_MESSAGES=[]

CLIENT_PORT=10005

MCAST_GRP = '224.1.1.1'
MCAST_PORT = 5007

def broadcast_socket (timeout=None):
    broadcast_socket =socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_address=("127.0.0.1", 0)
    broadcast_socket.bind(broadcast_address)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    if timeout:
        broadcast_socket.settimeout(timeout)
    return broadcast_socket

def setup_tcp_listener_socket():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("127.0.0.1", 0))
    server_socket.listen()
    return server_socket

def setup_client_socket():
    client_socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.bind(("127.0.0.1",0))
    return client_socket

def tcp_message(message, address):
    transmit_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transmit_socket.settimeout(1)
    transmit_socket.connect(address)
    transmit_socket.send(message)
    transmit_socket.close()

def encode_message(command, sender, contents='', clock=None):
    message_dict = {'command': command, 'sender': sender, 'contents': contents, 'clock': clock}
    return repr(message_dict).encode()