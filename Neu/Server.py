import socket
import Shared
import threading
import ast




BROADCASTCODE_SERVER='820734130907390'
BROADCASTCODE_SERVER_REPLY='482168278318180'


SERVER=Shared.unicast_TCP_listener()
SERVER_ADDRESS=SERVER.getsockname()

SERVER_LIST=[SERVER_ADDRESS]
CLIENT_LIST=[]

ISLEADER=False



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
        global ISLEADER
        ISLEADER=True
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
    while True:
        try:
            data, addr= SERVER.accept()     #accept the TCP connection
            recv_data=data.recv(1024)  #receive packages with buffer size of 1024
            msg=ast.literal_eval(recv_data.decode())
        except Exception as e:
            print (e)
        else:
            match msg:
                case {'Request_Type': 'Join', 'requester_type': requester_type, 'Address': addr}:
                    if requester_type == 'Server':
                        global SERVER_LIST
                        addr_add= (addr[0], addr[1])
                        print(addr_add)
                        SERVER_LIST.append(addr_add)
                        print(f'Server List: {SERVER_LIST}')
                        server_state=create_server_state()     #Server state is created = Serverlist, Clientlist, etc to be sent to the joining Server
                        server_state=repr(server_state).encode()    #Message gets encoded for TCP MSG
                        Shared.unicast_TCP_sender(server_state, addr)   #TCP MSG to joining Server

                        #The other Servers need the updated Serverlist, therefore it is sent to every Server besides the Leader and the joining Server
                        for i in range(len(SERVER_LIST)):
                            if SERVER_LIST[i]!=addr_add and SERVER_LIST[i] != SERVER_ADDRESS:
                                msg=f'[SERVER] The Server {addr_add} joined the server group'
                                Shared.unicast_TCP_sender(server_state, SERVER_LIST[i])
                                Shared.unicast_TCP_sender(server_state, SERVER_LIST[i])


                case {'Status': 'Status', 'Server_List': SERVER_LIST, 'Client_List': CLIENT_LIST}:
                    SERVER_LIST=msg['Server_List']
                    print(f'[SERVER] Received updated Server List {SERVER_LIST}')



def create_server_state():
    server_status = {'Status': 'Status', 'Server_List': SERVER_LIST, 'Client_List': CLIENT_LIST}
    return server_status


    print()



def server_handler(msg):
    match msg:
        case{'Request_Type': 'Join', 'requester_type': requester_type, 'Adddress': address}:
            if requester_type=='Server':
                #Multicast an Server

                #Übertragung von Serverliste/Clientliste an joinenden Server
                send_server_status = {'Status': 'Status', 'Server_List': SERVER_LIST, 'Client_List': CLIENT_LIST}
                Shared.unicast_TCP_sender(send_server_status, address)

            if requester_type=='Client':
                print()
                #Multicast an Clients

    print()
if __name__ == '__main__':
    broadcast_sender()
    threading.Thread(target=broadcast_listener).start()
    threading.Thread(target=tcp_listener).start()
