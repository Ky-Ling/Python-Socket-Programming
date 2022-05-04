from email import message
from os import execv
import sys
import socket
import selectors
import types
from . import libserver

sel = selectors.DefaultSelector()

host, port = sys.argv[1], int(sys.argv[2])
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Avoid bind() exception: OSError: [Errno 48] Address already in use
lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

lsock.bind((host, port))
lsock.listen()

print(f"Listening on {(host, port)}")

# Configure the socket in non-blocking mode
lsock.setblocking(False)
sel.register(lsock, selectors.EVENT_READ, data=None)


# Event Loop
try:
    while True:

        # sel.select(timeout=None) blocks until there are sockets ready for I/O. It returns a list of tuples, one for each socket. 
        # Each tuple contains a key and a mask.
        events = sel.select(timeout=None)

        #  key.fileobj is the socket object, and mask is an event mask of the operations that are ready.
        for key, mask in events:

            # The data is from the listening socket and we need to accept the connection
            if key.data is None:

                # Get the new socket object and register it with the selector
                accept_wrapper(key.fileobj)

            # It is a client socket that¡¯s already been accepted
            else:
                message = key.data
                
                try: 
                    message.process_events(mask)
                except Exception:
                    print(
                        f"Main: Error: Exception for {message.addr}:\n"
                        f"{traceback.format_exc()}"
                    )
                    message.close()



        def accept_wrapper(sock):

            # Because the listening socket was registered for the event selectors.EVENT_READ, it should be ready to read.
            conn, addr = sock.accept()
            print(f"Accepted connection from {addr}")
            
            # Put the socket in non-blocking mode.
            conn.setblocking(False)
            
            # When a client connection is accepted, a Message object is created:
            message = libserver.Message(sel, conn, addr)
            sel.register(conn, selectors.EVENT_READ, data=message)
        
        # How a client connection is handled when it¡¯s ready
        def service_connection(key, mask):
            sock = key.fileobj
            data = key.data

            if mask & selectors.EVENT_READ:

                # Should be ready to read
                recv_data = sock.recv(1024)

                if recv_data:
                    data.outb += recv_data
                
                # If no data is received, this means that the client has closed their socket, so the server should too.
                else:
                    print(f"Closing connection to {data.addr}")
                    sel.unregister(sock)
                    sel.close()

            if mask & selectors.EVENT_WRITE:
                if data.outb:
                    print(f"Echoing {data.outb!r} to {data.addr}")
                    
                    # Should be ready to write
                    sent = sock.send(data.outb)
                    data.outb = data.outb[sent:]
       
except KeyboardInterrupt:
    print("Caught keyboard interrupt, exiting")

finally:
    sel.close()



