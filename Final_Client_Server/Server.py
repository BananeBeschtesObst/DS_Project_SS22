import socket
import Shared
import threading
import ast
from time import sleep


MCAST_SERVER_GRP = '224.1.1.1'
MCAST_SERVER_PORT = 5007


BROADCASTCODE_SERVER='820734130907390'
BROADCASTCODE_SERVER_REPLY='482168278318180'


SERVER=Shared.unicast_TCP_listener()
SERVER_ADDRESS=SERVER.getsockname()

SERVER_LIST=[SERVER_ADDRESS]
CLIENT_LIST=[]
SERVER_LIST_RING=[]
MESSAGE_LIST=[]
CLOCK=0

ISLEADER=False
IS_ACTIVE=True

NEIGHBOR=None
LEADER_ADDRESS=None

VOTING=False


#Sending Broadcasts to find other Servers/Clients
def broadcast_sender():
    reply=False     #If the Server doesnt receive an answer it automatically declares itself as the leader

    broadcast_sender=Shared.broadcast_UDP_sender(timeout=2)     #Creating Broadcast Socket with timeout - So there is 2 Seconds between each Broadcast sent
    print (f'Sending Broadcast on {broadcast_sender.getsockname()}')

    br_addr=('<broadcast>', Shared.BROADCAST_PORT)

    for i in range (0,5):
        broadcast_sender.sendto(f'{BROADCASTCODE_SERVER},{SERVER_ADDRESS}'.encode(),br_addr)
        print(f'[SERVER] Sending broadcast message on [{br_addr[0]}, {br_addr[1]}]')

        #Waiting for answer of a Server
        try:
            data, addr= broadcast_sender.recvfrom(1024)
            if data.startswith(BROADCASTCODE_SERVER_REPLY.encode()):
                #Reply of the Server needs to be decoded in order to get the server address, that is needed for the join request
                replying_Server_IP=data.decode().split('#')[1]
                replying_Server_Port=data.decode().split('#')[2]
                replying_Server_Port=int(replying_Server_Port)  #Port needs to be an integer
                reply_address=(replying_Server_IP, replying_Server_Port)    #creating address for the request msg
                reply=True      #Server has received an answer of an already active Server, which means he has to join the existing server group
                msg=Shared.create_node('Join', 'Server', SERVER_ADDRESS)    #Creating Join Request that will be sent to the responding Server
                Shared.unicast_TCP_sender(repr(msg).encode(), reply_address)     #Sending the join request per TCP to the responding Server
                #leader_address=((addr[0], response_port))
                #setup_leader(leader_address)
                break
        except TimeoutError:
            pass

    if reply==False:
        global ISLEADER, LEADER_ADDRESS
        ISLEADER=True
        LEADER_ADDRESS=SERVER_ADDRESS
        print ('[SERVER] I am the leader')


    broadcast_sender.close()


def broadcast_listener():
    broadcast_listener=Shared.broadcast_UDP_listener()
    print(f'Listening for Broadcast on {broadcast_listener.getsockname()}')

    while True:
        try:
            data, addr = broadcast_listener.recvfrom(1024)
        except Exception as e:
            print(e)
            pass
        else:
            if data.startswith(BROADCASTCODE_SERVER.encode()) and ISLEADER is True:
                broadcast_listener.sendto(f'{BROADCASTCODE_SERVER_REPLY}#{SERVER_ADDRESS[0]}#{SERVER_ADDRESS[1]}'.encode(), addr)       #Sending the broadcasting Server the Broadcast_Server_Reply Code and the Server Address, that is needed for the join request


def multicast_sender():
    clock=0


def multicast_listener():
    print()

#Listener for incoming TCP Messages
def tcp_listener():
    global VOTING
    SERVER.settimeout(2)
    used=False
    print(f'Starting Server on {SERVER_ADDRESS}')
    while True:
        try:
            data, addr= SERVER.accept()     #accept the TCP connection
            recv_data=data.recv(4096)  #receive packages with buffer size of 1024
            msg=ast.literal_eval(recv_data.decode())
        except TimeoutError as e:
            pass
        else:
            global LEADER_ADDRESS, CLOCK, MESSAGE_LIST, CLIENT_LIST, SERVER_LIST
            match msg:
                case {'Message_Type': 'Chat','Username':username,'Message': message, 'Address': addr, 'Clock':clock}:
                    if SERVER_ADDRESS == LEADER_ADDRESS:
                        CLOCK += 1
                        msg['Clock'] = CLOCK
                        name = msg['Username']
                        msg_enc = msg['Message']
                        client_msg = f'{name}: {msg_enc}'
                        MESSAGE_LIST.append(msg)
                        print(MESSAGE_LIST)
                        send_client_msg(msg)

                        # I need to create a new server state as soon as a message of the clients is received, so that every server keeps track of the new messages.
                        # Otherwise if the server crashes, the other server maybe dont have all messages in the Message List
                        server_state = create_server_state()
                        for i in range(len(SERVER_LIST)):
                            if SERVER_LIST[i] != LEADER_ADDRESS:
                                try:
                                    Shared.unicast_TCP_sender(repr(server_state).encode(), SERVER_LIST[i])
                                except TimeoutError as e:
                                    pass

                case {'Message_Type': 'User', 'Username': username, 'Message': message, 'Address': address,
                      'Clock': clock}:
                    msg_client = Shared.create_msg_node('Join', f'{[msg["Username"]]} joined the chat room',
                                                        SERVER_ADDRESS)
                    for i in range(len(CLIENT_LIST)):
                        if CLIENT_LIST[i] != msg['Address']:
                            try:
                                Shared.unicast_TCP_sender(repr(msg_client).encode(), CLIENT_LIST[i])
                            except TimeoutError:
                                pass

                case {'Request_Type': 'Join', 'requester_type': requester_type, 'Address': addr}:
                    if requester_type == 'Server' and SERVER_ADDRESS==LEADER_ADDRESS:
                        addr_add= (addr[0], addr[1])
                        print(f'[SERVER] Added Server: {addr_add} to the server list')

                        if addr_add not in SERVER_LIST:     #No Duplicates in the Serverlist
                            SERVER_LIST.append(addr_add)
                        server_state=create_server_state()     #Server state is created = Serverlist, Clientlist, etc to be sent to the joining Server
                        server_state=repr(server_state).encode()    #Message gets encoded for TCP MSG
                        Shared.unicast_TCP_sender(server_state, addr)   #TCP MSG to joining Server
                        print(f'The current serverlist is: {SERVER_LIST}')


                        #The other Servers need the updated Serverlist, therefore it is sent to every Server besides the Leader and the joining Server
                        for i in range(len(SERVER_LIST)):
                            if SERVER_LIST[i]!=addr_add and SERVER_LIST[i] != SERVER_ADDRESS:
                                msg=Shared.create_msg_node('Server_Message', f'[SERVER] The Server {addr_add} joined the Server Group', SERVER_LIST[i])
                                Shared.unicast_TCP_sender(repr(msg).encode(), SERVER_LIST[i])
                                Shared.unicast_TCP_sender(server_state, SERVER_LIST[i])

                        get_neighbor()

                    if requester_type == 'Client' and SERVER_ADDRESS==LEADER_ADDRESS:
                        addr_add_client= (addr[0], addr[1])
                        print(f'[SERVER] Added Client: {addr_add_client} to the client list')
                        if addr_add_client not in CLIENT_LIST:
                            CLIENT_LIST.append(addr_add_client)
                        server_state=create_server_state()
                        server_state = repr(server_state).encode()  # Message gets encoded for TCP MSG
                        for i in range(len(SERVER_LIST)):
                            Shared.unicast_TCP_sender(server_state, SERVER_LIST[i])
                        print(f'The current Clientlist is: {CLIENT_LIST}')


                case {'Status': 'Status', 'Server_List': server_list, 'Client_List': client_list, 'Message_List': message_list,'Leader_Address': leader_address, 'Sender': address, 'Voting': voting, 'Message_Clock': clock}:
                        SERVER_LIST=msg['Server_List']
                        LEADER_ADDRESS=msg['Leader_Address']
                        CLIENT_LIST=msg['Client_List']
                        MESSAGE_LIST=msg['Message_List']
                        VOTING=msg['Voting']
                        CLOCK=msg['Message_Clock']

                        #print(f'[SERVER] Received Server List {SERVER_LIST} from {msg["Sender"]}')
                        #print(f'[SERVER] Received Client List {CLIENT_LIST} from {msg["Sender"]}')
                        #print(f'The leader is {LEADER_ADDRESS}')
                        print(f'Received current Server state')
                        get_neighbor()

                case{'Message_Type': server_message, 'Message': message, 'Address': addr}:
                    if server_message=='Server_Message':
                        serv_msg= msg['Message']
                        print(serv_msg)
                    if server_message == 'Victory':
                        serv_msg = msg['Message']
                        print(serv_msg)

                case{'Request_Type': 'Ping', 'requester_type': 'Server', 'Address': addr}:
                    print(f'ping from {msg["Address"]}')
                    test=0


                #As soon as a server is removed, the leader checks with the other servers if everybody else is still
                #there -> to be implemented with Multicast
                case {'Request_Type': 'Left', 'requester_type': 'Server', 'Address': address}:
                    if SERVER_ADDRESS==LEADER_ADDRESS:
                        sleep(1)
                        SERVER_LIST.remove(address)
                        server_state = create_server_state()
                        print(f'The current serverlist is: {SERVER_LIST}; The server {address} was removed from the serverlist')
                        for i in range(len(SERVER_LIST)):
                            if SERVER_LIST[i] != LEADER_ADDRESS:
                                try:
                                    Shared.unicast_TCP_sender(repr(server_state).encode(), SERVER_LIST[i])
                                except TimeoutError as e:
                                    pass

                #Another Server with a lower ID startet an election and is sending a Voting msg to this server
                #This Server - if active - then replies
                case{'Request_type': 'Voting', 'Address': addr}:
                    elect_leader()



def create_server_state():
    SERVER_LIST.sort()
    server_status = {'Status': 'Status', 'Server_List': SERVER_LIST, 'Client_List': CLIENT_LIST, 'Message_List': MESSAGE_LIST,'Leader_Address': LEADER_ADDRESS, 'Sender': SERVER_ADDRESS, "Voting": VOTING, 'Message_Clock': CLOCK}
    return server_status


#With this function each server can identify its neigbor based on the Serverlist that it received from the leader
#The Serverlist is maintained by the leader
#A Neigbor of a server is the server that is right to him in the list, the last server in the list has the server on
#list[0] as neighbor, making it therefore a ring
#The ring is used for leader election and hearbeat -> Crash fault tolerance
def get_neighbor():
    global NEIGHBOR
    if len(SERVER_LIST)==1:
        NEIGHBOR=None
        print('I have no Neighbor')
        return
    index=SERVER_LIST.index(SERVER_ADDRESS)
    NEIGHBOR= SERVER_LIST[0] if index+1 == len(SERVER_LIST) else SERVER_LIST[index+1]
    print(f'My Neighbor is {NEIGHBOR}')

#A heartbeat is sent from each server to its neighbor
#If the hearbeat cant be delivered the sending server knows that the server is no longer online and starts
#the fault tolerance procedure
#If its a normal server that disconnected (not the leader) then start a new leader election
def heartbeat():
    global NEIGHBOR, VOTING, LEADER_ADDRESS
    missed_beats=0
    new_leader_elected=False
    while IS_ACTIVE:
        new_leader_elected=False
        if VOTING==False:
            if NEIGHBOR:    #Heartbeat only starts if there is a neighbor
                try:
                    msg=Shared.create_node('Ping', 'Server', SERVER_ADDRESS)    #create ping msg
                    Shared.unicast_TCP_sender(repr(msg).encode(), NEIGHBOR)     #TCP to neighbor with the hearbeat
                    sleep(2)    #Time till the next tcp is sent
                except (ConnectionRefusedError, TimeoutError):      #if the msg doesnt receive the server
                    missed_beats+=1     #every time a msg cant be delivered 1 is added to missed beats
                    print(f'missed beats= {missed_beats}')
                if missed_beats>5:      #if 5 messages couldnt be delivered the procedure starts to deal with the disconnect
                    print(f"[SERVER] The Server {NEIGHBOR} isnt responding, Server is getting removed")
                    msg_del_server= Shared.create_node('Left', 'Server', NEIGHBOR)      #msg that the neighbor left the server group
                    missed_beats=0

                    #Msg is sent to the leader, if the server who discovered the disconnect of his neighbor isnt the leader
                    #or if the neighbor wasnt the leader (because then the leader cant receive the msg anyway)
                    #The leader who receives this msg takes care of the needed maintanance (delete not responding server
                    #from serverlist. Leader creates mew serverstate and sends it to the still active servers.
                    #The other servers receive the Status msg and also identify the new neighbor in the latest serverlist


                    if SERVER_ADDRESS !=LEADER_ADDRESS and NEIGHBOR != LEADER_ADDRESS:
                        count=0
                        while count<2:
                            try:
                                Shared.unicast_TCP_sender(repr(msg_del_server).encode(), LEADER_ADDRESS)
                                count=3
                            except TimeoutError as t:
                                print(f'{t} while trying to communicate with the leader')
                                count+=1
                                print(f'Count: {count}')
                            if count==2:
                                print('Cant reach leader - Starting new leader election')
                                for i in range(len(CLIENT_LIST)):
                                    client_msg = Shared.create_msg_node('Leader_Crash',
                                                                        'The Leader crashed, a new leader is elected, you can soon start chatting again',
                                                                        SERVER_ADDRESS)
                                    Shared.unicast_TCP_sender(repr(client_msg).encode(), CLIENT_LIST[i])
                                SERVER_LIST.remove(LEADER_ADDRESS)
                                SERVER_LIST.remove(NEIGHBOR)
                                LEADER_ADDRESS = ''
                                VOTING = True
                                server_state = create_server_state()
                                if len(SERVER_LIST) > 1:
                                    for i in range(len(SERVER_LIST)):
                                        if SERVER_LIST[i] != SERVER_ADDRESS:
                                            try:
                                                Shared.unicast_TCP_sender(repr(server_state).encode(), SERVER_LIST[i])
                                            except TimeoutError as t:
                                                print(t)
                                print(
                                    f'[SERVER] The disconnected Server {NEIGHBOR} was the leader, starting a new election')
                                elect_leader()
                                get_neighbor()
                                new_leader_elected=True
                                missed_beats=0




                    #If the server who discovers the disconnect of its neighbor is the leader himself he takes care of the
                    #maintanance here (because it wouldnt make sense to send himself a tcp to do that and i think probably
                    #not possible)
                    if SERVER_ADDRESS==LEADER_ADDRESS and new_leader_elected==False:
                        SERVER_LIST.remove(NEIGHBOR)
                        print(f'The current serverlist is: {SERVER_LIST}; The server {NEIGHBOR} was removed from the serverlist')

                        server_state = create_server_state()
                        if len(SERVER_LIST) > 1:
                            for i in range(len(SERVER_LIST)):
                                if SERVER_LIST[i] != LEADER_ADDRESS:

                                    try:
                                        Shared.unicast_TCP_sender(repr(server_state).encode(), SERVER_LIST[i])
                                    except TimeoutError as t:
                                        print(t)

                            get_neighbor()
                        else:
                            NEIGHBOR=None
                            get_neighbor()
                    #If a server discovers that the not responding server is the leader, a new leader election is startet
                    #to deal with the problem
                    if NEIGHBOR==LEADER_ADDRESS:

                        for i in range(len(CLIENT_LIST)):
                            client_msg=Shared.create_msg_node('Leader_Crash', 'The Leader crashed, a new leader is elected, you can soon start chatting again',SERVER_ADDRESS)
                            try:
                                Shared.unicast_TCP_sender(repr(client_msg).encode(), CLIENT_LIST[i])
                            except:
                                pass
                        SERVER_LIST.remove(NEIGHBOR)
                        LEADER_ADDRESS=''
                        VOTING=True
                        server_state = create_server_state()
                        if len(SERVER_LIST) > 1:
                            for i in range(len(SERVER_LIST)):
                                if SERVER_LIST[i] != SERVER_ADDRESS:
                                    try:
                                        Shared.unicast_TCP_sender(repr(server_state).encode(), SERVER_LIST[i])
                                    except TimeoutError as t:
                                        print(t)
                        print(f'[SERVER] The disconnected Server {NEIGHBOR} was the leader, starting a new election')
                        elect_leader()
                        get_neighbor()

def elect_leader():
    global NEIGHBOR, ISLEADER, LEADER_ADDRESS, VOTING
    if len(SERVER_LIST)==1:
        victory()
        return

    VOTING=True     #If the serverlist isnt just 1 server, Voting is set to be true, so heartbeat is stopped while the election takes place
    count=0     #Count is relevant for the replies of the servers with an higher ID
    server_with_higher_id=[i for i in SERVER_LIST if i>SERVER_ADDRESS]      #This Server is making a list with every Server in the Serverlist that has a higher ID that itself
    print(f'[SERVER] Sending my election msg to every Server with a higher ID {server_with_higher_id}')
    if len(server_with_higher_id)>0:   #Only if there is a server with a higher ID

        vote_msg=Shared.create_vote_msg('Voting', SERVER_ADDRESS)       #Voting msg is created

        #Voting msg is sent to every Server in the server_with_higher_id list
        for i in range(len(server_with_higher_id)):
            try:
                Shared.unicast_TCP_sender(repr(vote_msg).encode(), server_with_higher_id[i])    #TCP msg sent to each
            except TimeoutError:    #If there is a Timeouterror, we assume the server isnt online, when the connection works we assume the server is online and received the message
                count=+1
        if count==len(server_with_higher_id):   #If there is no connection possible with every server with a higher IP
            print('[SERVER] No Server with a hihgher ID is responding, so i declare myself Leader')  #Server declares itself leader
            victory()
            return
    else:
        print('[SERVER] There is no Server with a higher ID, therefore I am declaring myself Leader')
        victory()

def victory():
    global ISLEADER, LEADER_ADDRESS, VOTING
    LEADER_ADDRESS=SERVER_ADDRESS
    ISLEADER=True
    print('[LEADER] I am the new leader')
    VOTING=False
    server_state=create_server_state()
    vic_msg = Shared.create_msg_node("Victory", f"[VICTORY]: {SERVER_ADDRESS} won the election and is the new leader",
                                     SERVER_ADDRESS)

    print('[LEADER] Sending the latest server state to each of my members and starting heartbeat')
    print(f'The current serverlist is: {SERVER_LIST}')
    print(f'The current clientlist is: {CLIENT_LIST}')

    for i in range(len(SERVER_LIST)):
        if SERVER_LIST[i] != SERVER_ADDRESS:
            try:
                Shared.unicast_TCP_sender(repr(vic_msg).encode(), SERVER_LIST[i])
                Shared.unicast_TCP_sender(repr(server_state).encode(), SERVER_LIST[i])
            except TimeoutError as t:
                print(t)

    for i in range(len(CLIENT_LIST)):
        client_msg = Shared.create_msg_node('Victory',
                                            f'[{SERVER_ADDRESS}] I am the new leader, you can start chatting again',
                                            SERVER_ADDRESS)
        try:
            Shared.unicast_TCP_sender(repr(client_msg).encode(), CLIENT_LIST[i])
        except TimeoutError as t:
            print(t)

def send_client_msg(msg):
    MULTICAST_TTL = 2
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, MULTICAST_TTL)
    try:
        sock.sendto(f'{msg}'.encode(), (MCAST_SERVER_GRP, MCAST_SERVER_PORT))
    except Exception as e:
        print(f'Failed to send Message to the other Clients: {e}')
    finally:
        sock.close()






    #msg= Shared.create_node('Voting', 'Server', SERVER_ADDRESS )
    #Shared.unicast_TCP_sender(repr(msg).encode(), )


    print()






if __name__ == '__main__':
    broadcast_sender()
    threading.Thread(target=broadcast_listener).start()
    threading.Thread(target=tcp_listener).start()
    threading.Thread(target=heartbeat).start()
