import sys
import socket
import selectors
import types

sel = selectors.DefaultSelector()

host, port = sys.argv[1], int(sys.argv[2])
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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

                # Called with key and mask as arguments, and that¡¯s everything we need to operate on the socket.
                service_connection(key, mask)


        def accept_wrapper(sock):

            # Because the listening socket was registered for the event selectors.EVENT_READ, it should be ready to read.
            conn, addr = sock.accept()
            print(f"Accepted connection from {addr}")
            
            # Put the socket in non-blocking mode.
            conn.setblocking(False)
            
            # Create an object to hold the data that we want included along with the socket using a SimpleNamespace. 
            data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
            events = selectors.EVENT_READ | selectors.EVENT_WRITE
            sel.register(conn, events, data=data)

        
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



