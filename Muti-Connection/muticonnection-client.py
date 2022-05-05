import socket
import sys
import types
import selectors


sel = selectors.DefaultSelector()
messages = [b"Message 1 from client.", b"Message 2 from client."]


# num_conns is read from the command-line and is the number of connections to create to the server.
def start_connections(host, port, num_conns):
    server_addr = (host, port)

    for i in range(0, num_conns):
        connid = i + 1
        print(f"Starting connection {connid} to {server_addr}")

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Each socket is set to non-blocking mode.
        sock.setblocking(False)
        sock.connect_ex(server_addr)

        events = selectors.EVENT_READ | selectors.EVENT_WRITE

        # The data you want to store with the socket is created using SimpleNamespace.
        # Everything needed to keep track of what the client needs to send, has sent, and has received,
        #   including the total number of bytes in the messages, is stored in the object data.
        data = types.SimpleNamespace(
            connid=connid,
            msg_total=sum(len(m) for m in messages),
            recv_total=0,
            # The messages that the client will send to the server are copied
            messages=messages.copy(),
            outb=b"",
        )

        sel.register(sock, events, data=data)


"""
    The client keeps track of the number of bytes it's received from the server so that it can close its side of the connection.
When the server detects this, it closes its side of the connection too.

    The server expects the client to close its side of the connection when it's done sending messages. 
If the client doesn't close, the server will leave the connection open. In a real application, 
you may want to guard against this in your server by implementing a timeout to prevent client connections from accumulating 
if they don't send a request after a certain amount of time.
"""


def service_connection(key, mask):
    sock = key.fileobj
    data = key.data

    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)

        if recv_data:
            data.outb += recv_data
            print(f"Received {recv_data!r} from connection {data.connid}")
            data.recv_total = len(recv_data)

        else:
            print(f"Closing connection {data.connid}")

        if not recv_data or data.recv_total == data.msg_total:
            print(f"Closing connection {data.connid}")
            sock.unregister(sock)
            sock.close()

    if mask & selectors.EVENT_WRITE:
        if not data.outb and data.messages:
            data.outb = data.messages.pop(0)

        if data.outb:
            print(f"Echoing {data.outb!r} to {data.addr}")
            print(f"Sending {data.outb!r} to connection {data.connid}")
            sent = sock.send(data.outb)
            data.outb = data.outb[sent:]


if len(sys.argv) != 4:
    print(f"Usage: {sys.argv[0]} <host> <port> <num_connections>")
    sys.exit(1)

host, port, num_conns = sys.argv[1:4]
start_connections(host, int(port), int(num_conns))

try:
    while True:
        events = sel.select(timeout=1)
        if events:
            for key, mask in events:
                service_connection(key, mask)
        # Check for a socket being monitored to continue.
        if not sel.get_map():
            break
except KeyboardInterrupt:
    print("Caught keyboard interrupt, exiting")
finally:
    sel.close()