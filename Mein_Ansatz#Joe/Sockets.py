import socket
SERVER_LIST=[]

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
    server_socket.bind(("127.0.0.1", 0))
    server_socket.listen()
    return server_socket