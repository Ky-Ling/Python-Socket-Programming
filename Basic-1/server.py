import socket
import threading


HEADER = 64
PORT = 5050
# SERVER = "169.254.26.84"

# Get this IP address automatically
SERVER = socket.gethostbyname(socket.gethostname())
ADDRESS = (SERVER, PORT)
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDRESS)


# Handle all the communication between client and server
def handle_client(conn, addr):
    print(f"[NEW CONNECTION] { addr } connected")

    connected = True
    while connected:

        # We won't pass this line of code till we receive message from client

        # How long the message is coming(How many bytes we will pass )
        message_length = conn.recv(HEADER).decode(FORMAT)

        if message_length:
            message_length = int(message_length)
            message = conn.recv(message_length).decode(FORMAT)

            if message == DISCONNECT_MESSAGE:
                connected = False
            
            print(f"[{ addr }] { message }")

            # Send message to client from server
            conn.send("Message from server.".encode(FORMAT))
            


    conn.close()


def start():
    server.listen()
    print(f"[LISTENING] Server is listening on { SERVER }")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

        # How many threads are active on this process
        print("")
        print(f"[ACTIVE CONNECTION] {threading.activeCount() - 1}")



print("[STARTING] Server is starting....")
start()