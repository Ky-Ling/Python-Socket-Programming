import selectors
import struct


class Message:
    def __init__(self, selector, addr, sock):
        pass


    def process_events(self, mask):
        if mask & selectors.EVENT_READ:
            self.read()

        if mask & selectors.EVENT_WRITE:
            self.write()

    def read(self):

        # The ._read() method is called first. It calls socket.recv() to read data from the socket and store it in a receive buffer.
        self._read()

        if self._jsonheader_len is None:
            self.process_protoheader()

        if self._jsonheader_len is not None:
            if self.jsonheader is None:
                self.process_protoheader()

        if self.jsonheader:
            if self.request is None:
                self.process_request()

            
    def write(self):

        # Check for a request first
        if self.request:
            if not self.response_created:
                self.create_response()

        # The ._write() method calls socket.send() if there¡¯s data in the send buffer.
        self._write()


    def process_protoheader(self):
        headerlen = 2

        if len(self._recv_buffer) >= headerlen:

            # Use struct.unpack() to read the value, decode it, and store it in self._jsonheader_len. 
            self._jsonheader_len = struct.unpack(">H", self._recv_buffer[:headerlen])[0]
            
            # After processing the piece of the message it¡¯s responsible for, .process_protoheader() removes it from the receive buffer.
            self._recv_buffer = self._recv_buffer[headerlen:]


    def process_jsonheader(self):
        headerlen = self._jsonheader_len

        if len(self._recv_buffer) >= headerlen:

            # The method self._json_decode() is called to decode and deserialize the JSON header into a dictionary.
            self.jsonheader = self._json_decode(self._recv_buffer[:headerlen], "utf-8")
            
            # After processing the piece of the message that it¡¯s responsible for, process_jsonheader() removes it from the receive buffer.
            self._recv_buffer = self._recv_buffer[headerlen:]

            for request_header in (
                "byteorder",
                "content-length",
                "content-type",
                "content-encoding",
            ):
                if request_header not in self.jsonheader:
                    raise ValueError(f"Missing required header '{request_header}'.")


    def process_request(self):
            content_len = self.jsonheader["content-length"]

            if not len(self._recv_buffer) >= content_len:
                return
            
            data = self._recv_buffer[:content_len]
            self._recv_buffer = self._recv_buffer[content_len:]

            if self.jsonheader["content-type"] == "text/json":

                # Decode and deserialize
                encoding = self.jsonheader["content-encoding"]
                self.request = self._json_decode(data, encoding)
                print(f"Received request {self.request!r} from {self.addr}")
            else:
                # Binary or unknown content-type
                self.request = data
                print(
                f"Received {self.jsonheader['content-type']} "
                f"request from {self.addr}"
                )

            # Set selector to listen for write events, we're done reading.
            # Modify the selector to monitor write events only.                
            self._set_selector_events_mask("w")


    def create_response(self):
        if self.jsonheader["content-type"] == "text/json":
            response = self._create_response_json_content()

        else:
            # Binary or unknown content-type
            response = self._create_response_binary_content()
        
        message = self._create_message(**response)
        self.response_created = True
        
        # The response is appended to the send buffer. This is seen by and sent via ._write().
        self._send_buffer += message
    

    def _write(self):
        if self._send_buffer:
            print(f"Sending {self._send_buffer!r} to {self.addr}")

            try:
                # Should be ready to write
                sent = self.sock.send(self._send_buffer)
            except BlockingIOError:
                # Resource temporarily unavailable (errno EWOULDBLOCK)
                pass

            else:
                self._send_buffer = self._send_buffer[sent:]

                # Close when the buffer is drained. The response has been sent.
                if sent and not self._send_buffer:
                    self.close()

                    



