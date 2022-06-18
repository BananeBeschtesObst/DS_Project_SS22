import socket
import threading
import time
import struct

import Shared

client_socket = Shared.setup_client_socket()

def client_broadcast():
    global SERVER_ADRESS

    broadcast_socket=Shared.broadcast_socket(timeout=3)
    print (f"Client is broadcasting on {broadcast_socket.getsockname()}")
    connected= True
    while connected:
        broadcast_socket.sendto(f'{Shared.BROADCAST_CODE_CLIENT}_{client_socket.getsockname()[1]}'.encode(),('<broadcast>', Shared.BROADCAST_PORT))
        print("Client is looking for a chat server")

        try:
            data,addr= broadcast_socket.recvfrom(1024)
        except TimeoutError:
            pass
        else:
            if data.startswith(f'{Shared.BROADCAST_CODE_CLIENT}'.encode()):
                message=data.decode().split('_')
                SERVER_ADRESS=((addr[0], int(message[1])))
                print (f"Chat server was found at {SERVER_ADRESS} \n")
                break
    broadcast_socket.close()


def connect_with_server():
    global client_socket
    client_socket.connect(SERVER_ADRESS)
    client_address = client_socket.getsockname()
    print(f'Server: Hello and welcome to the chat. Your IP is {client_address[0]}.')
    client_socket.send('Join'.encode())
    username = input('Server: Please enter your username below.\n') # Add username
    print(f'Server: Hi {username}, you can start chatting now.')
    while True:
        msg=input("")
        try:
            client_socket.sendto((username + ': ' + msg).encode(), SERVER_ADRESS) # client_socket.send(msg.encode())

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
    sock.bind(('', Shared.MCAST_PORT))

    mreq = struct.pack("4sl", socket.inet_aton(Shared.MCAST_GRP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    while True:
        msg=sock.recv(10240)
        print(msg.decode())



client_broadcast()
threading.Thread(target=connect_with_server, args=()).start()
threading.Thread(target=setup_multicast_listener, args=()).start()





#receive_Multicast()
