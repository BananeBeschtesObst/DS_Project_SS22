import socket
import threading
import time
import struct

import Sockets
BROADCAST_PORT=10001
BROADCAST_CODE = '9310e231f20a07cb53d96b90a978163d'
FORMAT='utf-8'

SERVER_ADRESS=''
#client=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#client.connect(ADDR)

def client_broadcast():
    global SERVER_ADRESS

    broadcast_socket=Sockets.broadcast_socket(timeout=3)
    print (f"Client Broadcast on {broadcast_socket.getsockname()}")
    connected= True
    while connected:
        broadcast_socket.sendto(f'{Sockets.BROADCAST_CODE_CLIENT}_{broadcast_socket.getsockname()[1]}'.encode(),('<broadcast>', BROADCAST_PORT))
        print("Client looking for Server")

        try:
            data,addr= broadcast_socket.recvfrom(1024)
        except TimeoutError:
            pass
        else:
            if data.startswith(f'{Sockets.BROADCAST_CODE_CLIENT}'.encode()):
                message=data.decode().split('_')
                SERVER_ADRESS=((addr[0], int(message[1])))
                print (f"Found Server at {SERVER_ADRESS}")
                break
    broadcast_socket.close()


def connect_with_server():
    global client_socket
    client_socket=Sockets.setup_client_socket()
    client_socket.connect(SERVER_ADRESS)

    client_address = client_socket.getsockname()
    print(f'[{SERVER_ADRESS[0]}, {SERVER_ADRESS[1]}]: Hi, welcome to the chat {client_address[0]}, {client_address[1]}')
    client_socket.send('Join'.encode())
    print('You can start chatting now')
    while True:
        msg=input("")
        try:
            client_socket.send(msg.encode())
        except Exception as e:
            print (e)
            break


def check_leader():
    global client_socket

    while True:
        try:
            data=client_socket.recv(1024)
            print(data.decode('utf-8'))

            if not data:
                ("Cant reach Chat Server, pls wait 3 Seconds for reconnection with new Server")
                client_socket.close()
                time.sleep(3)
                connect_with_server()

        except Exception as e:
            print (e)
            break

def setup_multicast_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', Sockets.MCAST_PORT))

    mreq = struct.pack("4sl", socket.inet_aton(Sockets.MCAST_GRP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    sequence_number=0

    while True:
        msg=sock.recv(10240)
        nummer = int(msg.decode().split('_')[1])
        msg1 = int(msg.decode().split('_')[2])

        if sequence_number !=nummer:
            # For Python 3, change next line to "print(sock.recv(10240))"
            print(msg1)
            sequence_number=nummer




client_broadcast()
threading.Thread(target=connect_with_server, args=()).start()
threading.Thread(target=setup_multicast_listener, args=()).start()





#receive_Multicast()
