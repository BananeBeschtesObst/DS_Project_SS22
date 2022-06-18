import pickle
import socket
import threading

import Shared

is_leader = False

SERVER =Shared.setup_tcp_listener_socket()
SERVER_ADDRESS=SERVER.getsockname()
Shared.SERVER_LIST.append(SERVER_ADDRESS)

NEIGHBOR=None

print(f"Server runs on {SERVER_ADDRESS}")

#We use a broadcast to look for another active server
def broadcast ():

    #Create Socket
    broadcast_socket=Shared.broadcast_socket(timeout=1)

    #For loop to enable more than one attempt of finding another server
    for i in range (0,3):
        broadcast_socket.sendto(f'{Shared.BROADCAST_CODE}_{SERVER_ADDRESS}'.encode(), ('<broadcast>', Shared.BROADCAST_PORT))
        print(f"Sending Broadcast message on Port {Shared.BROADCAST_PORT} with {Shared.BROADCAST_CODE}")
        reply=False

        #Now we wait for a response packet. If no packet is received within 1 Second, broadcast again
        try:
            data, addr= broadcast_socket.recvfrom(1024)
            if data.startswith(f'Was geht ab'.encode()):
                print("Found Server on ", addr[0])
                response_port = int (data.decode().split('_')[2])
                Shared.SERVER_LIST.append(SERVER_ADDRESS)
                print(f"In der Liste ist/sind {len(Shared.SERVER_LIST)} Server")
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
    listen_socket.bind(('127.0.0.1', Shared.BROADCAST_PORT))

    active=True
    while active:
        try:
            data, addr = listen_socket.recvfrom(1024)
        except Exception as e:
            print(e)
            pass
        else:
            if is_leader and data.startswith(Shared.BROADCAST_CODE.encode()):
                print(f"Received Broadcast from {addr[0]} {addr[1]}, replying with Response code")
                listen_socket.sendto(str.encode(f"Was geht ab _{addr[0]}_{SERVER_ADDRESS[1]}"), addr)
                response_port_server = int (data.decode().split('_')[2])
                server_adress=(addr[0], response_port_server)
                Shared.SERVER_LIST.append(server_adress)
                send_server_list()
                print(f"Aktuelle Serverliste: {Shared.SERVER_LIST}")
            if is_leader and data.startswith(Shared.BROADCAST_CODE_CLIENT.encode()):
                print(f"Received Broadcast from {addr[0]}, replying with Response code")
                listen_socket.sendto(str.encode(f"{Shared.BROADCAST_CODE_CLIENT}{addr[0]}_{SERVER_ADDRESS[1]}"), addr)
                response_port_client = int(data.decode().split('_')[1])
                client_adress = (addr[0], response_port_client)
                Shared.CLIENT_LIST.append(client_adress)
        find_neighbors()

    print('Closing Broadcast Listener')
    listen_socket.close()


def setup_leader(address):
    global is_leader
    leader_address = address
    is_leader=leader_address ==SERVER_ADDRESS
    LEADER=address
    if is_leader:
        print("This server acts as the leader")

    else:
        print("An other server acts as the leader")

def connect_client():

    while True:
        try:
            data, addr= SERVER.accept()
            client_data=data.recv(1024)
            if addr in Shared.CLIENT_LIST:
                print("New client was found")
                print(f'[{SERVER_ADDRESS}]: New Client connection from {addr}')
                print(f"[Aktuelle Clients: {Shared.CLIENT_LIST}]")
                thread = threading.Thread(target=receive_client_message, args=(data, addr))
                thread.start()
            else:
                print("New server was found")
                a=pickle.loads(client_data)
                print(a)
        except Exception as e:
            print (e)
            break
    print('TCP listener closing')
    SERVER.close()

def receive_client_message (client, addr):
    while True:
            data = client.recv(1024)
            msg=data.decode('utf-8')
            if msg!='':
                print(f'{SERVER_ADDRESS[0]}: New Message from client {addr[0]}: {msg}')
                Shared.CLIENT_MESSAGES.append(f'{SERVER_ADDRESS[0]}: New Message from client {addr[0]}: {msg}')
                send_client_message(msg, addr)

def send_client_message(msg, addr):
    MULTICAST_TTL = 2
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, MULTICAST_TTL)
    try:
        sock.sendto(f'{msg}'.encode(), (Shared.MCAST_GRP, Shared.MCAST_PORT))
    except Exception as e:
        print(f'Failed to send Message to the other Clients: {e}')
    finally:
        sock.close()

def send_server_list ():
    print(f'abc {Shared.SERVER_LIST}')
    for i in range(len(Shared.SERVER_LIST)):
        if is_leader:
            addr=Shared.SERVER_LIST[i]
            print(f'addr {addr}')
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(addr)
            print(f'hier{Shared.SERVER_LIST}')
            data = pickle.dumps(Shared.SERVER_LIST)
            sock.send(data)


def find_neighbors():
    global NEIGHBOR
    length= len(Shared.SERVER_LIST)
    if length==1:
        NEIGHBOR=None
        print('I have no Neighbor')
        return
    Shared.SERVER_LIST.sort()
    print(Shared.SERVER_LIST)
    print (SERVER_ADDRESS)
    index=Shared.SERVER_LIST.index(SERVER_ADDRESS)
    print(index)




broadcast()
threading.Thread(target=broadcast_listener).start()
threading.Thread(target=connect_client).start()
#threading.Thread(target=send_server_list).start()

