import socket
import Sockets
BROADCAST_PORT=10001
BROADCAST_CODE = '9310e231f20a07cb53d96b90a978163d'
FORMAT='utf-8'

SERVER_ADRESS=''
#client=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#client.connect(ADDR)

def client_broadcast():
    global SERVER_ADRESS

    broadcast_socket=Sockets.broadcast_socket(timeout=3)
    print (f"Client Broadcast on {broadcast_socket.getsockname()}")
    connected= True
    while connected:
        broadcast_socket.sendto(BROADCAST_CODE.encode(),('<broadcast>', BROADCAST_PORT))
        print("Client looking for Server")

        try:
            data,addr= broadcast_socket.recvfrom(1024)
        except TimeoutError:
            pass
        else:
            if data.startswith(f'Was geht ab'.encode()):
                message=data.decode().split('_')
                SERVER_ADRESS=((addr[0], int(message[1])))
                print (f"Found Server at {SERVER_ADRESS}")
                break
    broadcast_socket.close()

client_broadcast()
