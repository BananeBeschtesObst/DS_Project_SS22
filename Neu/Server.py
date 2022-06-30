import socket
import Shared
import threading
import ast
from time import sleep





BROADCASTCODE_SERVER='820734130907390'
BROADCASTCODE_SERVER_REPLY='482168278318180'


SERVER=Shared.unicast_TCP_listener()
SERVER_ADDRESS=SERVER.getsockname()

SERVER_LIST=[SERVER_ADDRESS]
CLIENT_LIST=[]
SERVER_LIST_RING=[]

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

    for i in range (0,3):
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



def tcp_sender():
    print()

#Listener for incoming TCP Messages
def tcp_listener():
    SERVER.settimeout(2)

    while True:
        try:
            data, addr= SERVER.accept()     #accept the TCP connection
            recv_data=data.recv(1024)  #receive packages with buffer size of 1024
            msg=ast.literal_eval(recv_data.decode())
        except TimeoutError as e:
            pass
        else:
            match msg:
                case {'Request_Type': 'Join', 'requester_type': requester_type, 'Address': addr}:
                    if requester_type == 'Server':
                        global SERVER_LIST
                        addr_add= (addr[0], addr[1])
                        print(f'[SERVER] Added Server: {addr_add} to the server list')

                        if addr_add not in SERVER_LIST:     #No Duplicates in the Serverlist
                            SERVER_LIST.append(addr_add)
                        server_state=create_server_state()     #Server state is created = Serverlist, Clientlist, etc to be sent to the joining Server
                        server_state=repr(server_state).encode()    #Message gets encoded for TCP MSG
                        Shared.unicast_TCP_sender(server_state, addr)   #TCP MSG to joining Server


                        #The other Servers need the updated Serverlist, therefore it is sent to every Server besides the Leader and the joining Server
                        for i in range(len(SERVER_LIST)):
                            if SERVER_LIST[i]!=addr_add and SERVER_LIST[i] != SERVER_ADDRESS:
                                msg=Shared.create_msg_node('Server_Message', f'[SERVER] The Server {addr_add} joined the Server Group', SERVER_LIST[i])
                                Shared.unicast_TCP_sender(repr(msg).encode(), SERVER_LIST[i])
                                Shared.unicast_TCP_sender(server_state, SERVER_LIST[i])

                        get_neighbor()


                case {'Status': 'Status', 'Server_List': SERVER_LIST, 'Client_List': CLIENT_LIST, 'Leader_Address': leader_address}:
                    global LEADER_ADDRESS
                    SERVER_LIST=msg['Server_List']
                    LEADER_ADDRESS=msg['Leader_Address']
                    print(f'[SERVER] Received Server List {SERVER_LIST}')
                    print(f'The leader is {LEADER_ADDRESS}')
                    get_neighbor()

                case{'Message_Type': 'Server_Message', 'Message': message, 'Address': addr}:
                    serv_msg= msg['Message']
                    print(serv_msg)

                case{'Request_Type': 'Ping', 'requester_type': 'Server', 'Address': addr}:
                    print(f'ping from {msg["Address"]}')


                #As soon as a server is removed, the leader checks with the other servers if everybody else is still
                #there -> to be implemented with Multicast
                case {'Request_Type': 'Left', 'requester_type': 'Server', 'Address': addr}:
                    SERVER_LIST.remove(addr)
                    server_state = create_server_state()
                    for i in range(len(SERVER_LIST)):
                        if SERVER_LIST[i] != LEADER_ADDRESS:
                            try:
                                Shared.unicast_TCP_sender(repr(server_state).encode(), SERVER_LIST[i])
                            except TimeoutError as e:
                                print(e)








def create_server_state():
    SERVER_LIST.sort()
    server_status = {'Status': 'Status', 'Server_List': SERVER_LIST, 'Client_List': CLIENT_LIST, 'Leader_Address': LEADER_ADDRESS}
    return server_status


    print()

#With this function each server can identify its neigbor based on the Serverlist that it received from the leader
#The Serverlist is maintained by the leader
#A Neigbor of a server is the server that is right to him in the list, the last server in the list has the server on
#list[0] as neighbor, making it therefore a ring
#The ring is used for leader election and hearbeat -> Crash fault tolerance
def get_neighbor():
    global NEIGHBOR
    index=SERVER_LIST.index(SERVER_ADDRESS)
    NEIGHBOR= SERVER_LIST[0] if index+1 == len(SERVER_LIST) else SERVER_LIST[index+1]
    print(f'My Neighbor is {NEIGHBOR}')

#A heartbeat is sent from each server to its neighbor
#If the hearbeat cant be delivered the sending server knows that the server is no longer online and starts
#the fault tolerance procedure
#If its a normal server that disconnected (not the leader) then start a new leader election
def heartbeat():
    global NEIGHBOR
    missed_beats=0

    while IS_ACTIVE:
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
                    Shared.unicast_TCP_sender(repr(msg_del_server).encode(), LEADER_ADDRESS)

                #If the server who discovers the disconnect of its neighbor is the leader himself he takes care of the
                #maintanance here (because it wouldnt make sense to send himself a tcp to do that and i think probably
                #not possible)
                if SERVER_ADDRESS==LEADER_ADDRESS:
                    SERVER_LIST.remove(NEIGHBOR)
                    server_state = create_server_state()
                    if len(SERVER_LIST) > 1:
                        for i in range(len(SERVER_LIST)):
                            if SERVER_LIST[i] != LEADER_ADDRESS:
                                Shared.unicast_TCP_sender(repr(server_state).encode(), SERVER_LIST[i])
                        get_neighbor()
                    else:
                        NEIGHBOR=None

                #If a server discovers that the not responding server is the leader, a new leader election is startet
                #to deal with the problem
                if NEIGHBOR==LEADER_ADDRESS:
                    print(f'The disconnected Server {NEIGHBOR} was the leader, starting a new election')
                    elect_leader()

def elect_leader():



    print()

if __name__ == '__main__':
    broadcast_sender()
    threading.Thread(target=broadcast_listener).start()
    threading.Thread(target=tcp_listener).start()
    threading.Thread(target=heartbeat).start()
