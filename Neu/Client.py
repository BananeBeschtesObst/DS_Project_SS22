import socket
import threading
import time
import Shared
import ast

BROADCASTCODE_SERVER='820734130907390'
BROADCASTCODE_SERVER_REPLY='482168278318180'

LEADER_REACHABLE=False
active= True
CLIENT= Shared.unicast_TCP_listener()
CLIENT_ADDRESS=CLIENT.getsockname()

SERVER_ADDRESS=''
LEADER_ELECTED=True
USERNAME=''

def client_broadcast(): # creates a broadcast socket for the client to find a chat server in the network
    global SERVER_ADDRESS, LEADER_REACHABLE
    broadcast_sender=Shared.broadcast_UDP_sender(timeout=2)
    br_addr = ('<broadcast>', Shared.BROADCAST_PORT)


    while active:
        broadcast_sender.sendto(f'{BROADCASTCODE_SERVER},{CLIENT_ADDRESS}'.encode(),br_addr)
        print(f"Looking for Server on Broadcast Address: {broadcast_sender.getsockname()}")
        try:
            data,addr= broadcast_sender.recvfrom(1024)
        except TimeoutError:
            pass
        else:
            if data.startswith(f'{BROADCASTCODE_SERVER_REPLY}'.encode()):
                replying_Server_IP = data.decode().split('#')[1]
                replying_Server_Port = data.decode().split('#')[2]
                replying_Server_Port = int(replying_Server_Port)  # Port needs to be an integer
                reply_address = (replying_Server_IP, replying_Server_Port)  # creating address for the request msg
                print(f'Found Server on {reply_address}')
                set_server_address(reply_address)
                LEADER_REACHABLE=True
                break
    join_request = Shared.create_node('Join', 'Client', CLIENT_ADDRESS)
    Shared.unicast_TCP_sender(repr(join_request).encode(),reply_address)  # Sending the join request per TCP to the responding Server


def set_server_address(address):
    global SERVER_ADDRESS
    SERVER_ADDRESS=address

def connect_with_server(): # connecto to server giving username, start chatting to server's TCP port
    global LEADER_REACHABLE, USERNAME, active
    clock=None

    while len(USERNAME)<3:
        USERNAME = input('Server: Please enter your username below.\n') # Add username
        if len(USERNAME)>=3:
            msg_user = Shared.create_chat_msg_node('User', '', USERNAME, CLIENT_ADDRESS, '')
            Shared.unicast_TCP_sender(repr(msg_user).encode(), SERVER_ADDRESS)
            break
        else:
            print("[ERROR]: Your Username must have at least 3 Characters, please try again")

    print(f'\nWelcome to the chat {USERNAME}, you can start chatting now')
    while LEADER_REACHABLE is True and active:
        msg=input()

        if len(msg)>0:
            if len(msg)>4096/10:
                print('Your message is too long')
            else:
                client_msg= Shared.create_chat_msg_node('Chat', msg , USERNAME, CLIENT_ADDRESS, clock)
                try:
                    Shared.unicast_TCP_sender(repr(client_msg).encode(), SERVER_ADDRESS)
                except (ConnectionRefusedError, TimeoutError):
                    print("Server is not reachable at the moment")
                    LEADER_REACHABLE = False
    else:
        print('Leader not reachable')
        stop_client()

    print('Client is shutting down')



def setup_multicast_listener(): # client multicast listener to listen to chat messages from server
    already_sent=[]
    multicast_listener=Shared.multicast_UDP_listener()
    while active:
            recv_msg=multicast_listener.recv(4096)
            msg= ast.literal_eval(recv_msg.decode())
            clock = msg['Clock']
            if clock not in already_sent:
                already_sent.append(clock)
                print(f'{msg["Username"]}: {msg["Message"]}')

    multicast_listener.close()
    print("Closing Multicast Listener")

def tcp_listener():
    global LEADER_REACHABLE, SERVER_ADDRESS
    while active:
        try:
            data, addr= CLIENT.accept()     #accept the TCP connection
            recv_data=data.recv(4096)  #receive packages with buffer size of 1024
            msg=ast.literal_eval(recv_data.decode())
        except TimeoutError as e:
            pass
        else:
            match msg:
                case {'Message_Type': msg_type,'Message': message, 'Address': addr}:
                    if msg_type=='Leader_Crash':
                        LEADER_REACHABLE = False
                        serv_msg = msg['Message']
                        address = msg ['Address']
                        print(f'[{address}]: {serv_msg}')
                    if msg_type=='Victory':
                        serv_msg = msg['Message']
                        address = msg['Address']
                        SERVER_ADDRESS=address
                        LEADER_REACHABLE=True
                        print(f'[{address}]: {serv_msg}')
                    if msg_type=='Join':
                        serv_msg = msg['Message']
                        address = msg['Address']
                        print(f'[{address}]: {serv_msg}')


def stop_client():
    global active
    active =False



client_broadcast()
threading.Thread(target=connect_with_server, args=()).start()
threading.Thread(target=setup_multicast_listener, args=()).start()
threading.Thread(target=tcp_listener).start()




