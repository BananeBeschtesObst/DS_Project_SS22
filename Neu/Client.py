import socket
import threading
import time
import Shared
import ast

BROADCASTCODE_SERVER='820734130907390'
BROADCASTCODE_SERVER_REPLY='482168278318180'


CLIENT= Shared.unicast_TCP_listener()
CLIENT_ADDRESS=CLIENT.getsockname()

SERVER_ADDRESS=''
LEADER_ELECTED=True

def client_broadcast(): # creates a broadcast socket for the client to find a chat server in the network
    global SERVER_ADDRESS
    broadcast_sender=Shared.broadcast_UDP_sender(timeout=2)
    br_addr = ('<broadcast>', Shared.BROADCAST_PORT)


    while True:
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
                break
    join_request = Shared.create_node('Join', 'Client', CLIENT_ADDRESS)
    Shared.unicast_TCP_sender(repr(join_request).encode(),reply_address)  # Sending the join request per TCP to the responding Server


def set_server_address(address):
    global SERVER_ADDRESS
    SERVER_ADDRESS=address

def connect_with_server(): # connecto to server giving username, start chatting to server's TCP port

    username = input('Server: Please enter your username below.\n') # Add username

    while True:
        msg=input()

        if len(msg)>0:
            if len(msg)>4096/10:
                print('Your message is too long')
            else:
                client_msg= Shared.create_chat_msg_node('Chat', msg , username, CLIENT_ADDRESS)
                try:
                    Shared.unicast_TCP_sender(repr(msg).encode(), SERVER_ADDRESS)
                except (ConnectionRefusedError, TimeoutError):
                    print("Server is not reachable at the moment")
        else:
            continue


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

def setup_multicast_listener(): # client multicast listener to listen to chat messages from server
    mulicast_listener=Shared.multicast_UDP_listener()


    while True:
        recv_msg=mulicast_listener.recv(4096)
        msg= ast.literal_eval(recv_msg.decode())



client_broadcast()
threading.Thread(target=connect_with_server, args=()).start()
threading.Thread(target=setup_multicast_listener, args=()).start()



"""""

client_broadcast()
