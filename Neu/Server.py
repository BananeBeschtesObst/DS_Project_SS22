import socket
import Shared

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
                print("Found Server on ", data.decode().split(','))
                reply=True      #Server has received an answer of an already active Server, which means he has to join the existing server group

                #response_port = int (data.decode().split('_')[2])
                #Shared.SERVER_LIST.append(SERVER_ADDRESS)
                #print(f"In der Liste ist/sind {len(Shared.SERVER_LIST)} Server")
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
            if data.startswith(BROADCASTCODE_SERVER.encode()):
                broadcast_listener.sendto(f'{BROADCASTCODE_SERVER_REPLY},{SERVER_ADDRESS}'.encode(), (addr))

if __name__ == '__main__':
    broadcast_sender()
    broadcast_listener()