import socket
import threading
import pickle
import Sockets
from Sockets import broadcast_socket
is_leader = False
HEADER=64
PORT= 0
SERVER=socket.gethostbyname(socket.gethostname())
ADDR=(SERVER,PORT)
FORMAT='utf-8'
DISCONNECT_MESSAGE="!DISCONNECT"

BROADCAST_PORT=10001
BROADCAST_CODE = '9310e231f20a07cb53d96b90a978163d'

server =Sockets.setup_tcp_listener_socket()
SERVER_ADDRESS=server.getsockname()


LEADER=''


print(f"Server runs on {SERVER_ADDRESS}")


def handle_client(conn, addr):
    print (f"[NEW CONNECTION]{addr} conenected")

    connected=True
    while connected:
        #msg_length=conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length=int(msg_length)
            msg= conn.recv(msg_length).decode(FORMAT)
            if msg==DISCONNECT_MESSAGE:
                connected=False

            print(f"[{addr}] {msg}")
            conn.send("Msg received".encode(FORMAT))

    conn.close()






def start ():
    server.listen()
    while True:
        conn, addr = server.accept()
        thread=threading.Thread(target=handle_client, args=(conn,addr))
        thread.start()
        print(f" [ACTIVE CONNECTIONS] {threading.active_count()-1}")

#We use a broadcast to look for another active server
def broadcast ():

    #Create Socket
    broadcast_socket=Sockets.broadcast_socket(timeout=1)

    #For loop to enable more than one attempt of finding another server
    for i in range (0,3):
        broadcast_socket.sendto(f'{BROADCAST_CODE}_{SERVER_ADDRESS[1]}'.encode(), ('<broadcast>', BROADCAST_PORT))
        print(f"Sending Broadcast message on Port {BROADCAST_PORT} with {BROADCAST_CODE}")
        reply=False

        #Now we wait for a response packet. If no packet is received within 1 Second, broadcast again
        try:
            data, addr= broadcast_socket.recvfrom(1024)
            if data.startswith(f'Was geht ab'.encode()):
                print("Found Server on ", addr[0])
                response_port = int (data.decode().split('_')[1])
                Sockets.SERVER_LIST.append(SERVER_ADDRESS)
                print(f"In der Liste ist/sind {len(Sockets.SERVER_LIST)} Server")
                leader_address=((addr[0], response_port))
                reply=True
                setup_leader(leader_address)
                break
        except TimeoutError:
            pass

    broadcast_socket.close()
    if not reply:
        print('No other servers found')
        setup_leader(SERVER_ADDRESS)


def broadcast_listener():
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_socket.bind(('127.0.0.1', BROADCAST_PORT))

    listen_address= listen_socket.getsockname()

    print(f"Listening to Broadcast messages {listen_address}")
    active=True
    while active:
        try:
            data, addr = listen_socket.recvfrom(1024)
            print(data.decode(FORMAT))
            print(is_leader)
        except TimeoutError:
            pass
        else:
            if is_leader and data.startswith(BROADCAST_CODE.encode()):
                print(f"Received Broadcast from {addr[0]}, replying with Response code")
                listen_socket.sendto(str.encode(f"Was geht ab{addr[0]}_{SERVER_ADDRESS[1]}"), addr)
                response_port = int (data.decode().split('_')[1])
                server_adress=(addr[0], response_port)
                Sockets.SERVER_LIST.append(server_adress)
                print (len(Sockets.SERVER_LIST))

    print('Closing Broadcast Listener')
    listen_socket.close()


def setup_leader(address):
    global is_leader
    leader_address = address
    is_leader=leader_address ==SERVER_ADDRESS
    if is_leader:
        print("Ich bin der Leader")

    else:
        print("Jemand anderes ist der Leader")


broadcast()

threading.Thread(target=broadcast_listener).start()

start ()
