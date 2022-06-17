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

SERVER =Sockets.setup_tcp_listener_socket()
SERVER_ADDRESS=SERVER.getsockname()
Sockets.SERVER_LIST.append(SERVER_ADDRESS)

BROADCAST_CODE_Client='Nicetomeetyou'

LEADER=''

msg_sequence_number = 0

print(f"Server runs on {SERVER_ADDRESS}")



#We use a broadcast to look for another active server
def broadcast ():

    #Create Socket
    broadcast_socket=Sockets.broadcast_socket(timeout=1)

    #For loop to enable more than one attempt of finding another server
    for i in range (0,3):
        broadcast_socket.sendto(f'{BROADCAST_CODE}_{SERVER_ADDRESS[0]}_{SERVER_ADDRESS[1]}'.encode(), ('<broadcast>', BROADCAST_PORT))
        print(f"Sending Broadcast message on Port {BROADCAST_PORT} with {BROADCAST_CODE}")
        reply=False

        #Now we wait for a response packet. If no packet is received within 1 Second, broadcast again
        try:
            data, addr= broadcast_socket.recvfrom(1024)
            if data.startswith(f'Was geht ab'.encode()):
                print("Found Server on ", addr[0])
                response_port = int (data.decode().split('_')[2])
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
    print(f'Server up and running at {SERVER_ADDRESS}')
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_socket.bind(('127.0.0.1', BROADCAST_PORT))

    active=True
    while active:
        try:
            data, addr = listen_socket.recvfrom(1024)
        except Exception as e:
            print(e)
            pass
        else:
            if is_leader and data.startswith(BROADCAST_CODE.encode()):
                print(f"Received Broadcast from {addr[0]} {addr[1]}, replying with Response code")
                listen_socket.sendto(str.encode(f"Was geht ab _{addr[0]}_{SERVER_ADDRESS[1]}"), addr)
                response_port_server = int (data.decode().split('_')[2])
                server_adress=(addr[0], response_port_server)
                Sockets.SERVER_LIST.append(server_adress)
                print(f"Aktuelle Serverliste: {Sockets.SERVER_LIST}")
            if is_leader and data.startswith(BROADCAST_CODE_Client.encode()):
                print(f"Received Broadcast from {addr[0]}, replying with Response code")
                listen_socket.sendto(str.encode(f"{Sockets.BROADCAST_CODE_CLIENT}{addr[0]}_{SERVER_ADDRESS[1]}"), addr)
                response_port_client = int(data.decode().split('_')[1])
                client_adress = (addr[0], response_port_client)
                Sockets.CLIENT_LIST.append(client_adress)


    print('Closing Broadcast Listener')
    listen_socket.close()


def setup_leader(address):
    global is_leader
    leader_address = address
    is_leader=leader_address ==SERVER_ADDRESS
    LEADER=address
    if is_leader:
        print("Ich bin der Leader")

    else:
        print("Jemand anderes ist der Leader")

def connect_client():

    while True:
        #try:
            data, addr= SERVER.accept()
            client_data=data.recv(1024)

            if client_data:
                print (f'[{SERVER_ADDRESS[0]}, {SERVER_ADDRESS[1]}]: New Client connection {addr[0]}, {addr[1]}')
                thread = threading.Thread(target=receive_client_message, args=(data, addr))
                thread.start()
    #except Exception as e:
            #print (e)
            #break


def receive_client_message (client, addr):
    while True:
        #try:
            data = client.recv(1024)
            msg=data.decode('utf-8')
            if msg!='':
                print(f'{SERVER_ADDRESS[0]}: New Message from {addr[0]}: {msg}')
                Sockets.CLIENT_MESSAGES.append(f'{SERVER_ADDRESS[0]}: New Message from {addr[0]}: {msg}')
                send_client_message(msg, addr)

        #except Exception as e:
            #print(e)
            #break

def send_client_message(msg, addr):
    global msg_sequence_number
    print(f'hier {msg_sequence_number}')
    MULTICAST_TTL = 2
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, MULTICAST_TTL)
    msg_sequence_number=msg_sequence_number+1
    sock.sendto(f'_{msg_sequence_number}_{addr[0]} {addr[1]}] sent: {msg}'.encode(), (Sockets.MCAST_GRP, Sockets.MCAST_PORT))
    print(msg_sequence_number)

broadcast()
threading.Thread(target=broadcast_listener).start()
connect_client()

