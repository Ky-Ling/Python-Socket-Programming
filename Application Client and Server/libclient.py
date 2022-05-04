class Message:
    def __init__(self, selector, addr, conn, request) -> None:
        pass


    def write(self):

        # Because the client initiates a connection to the server and sends a request first, the state variable _request_queued is checked
        if not self._request_queued:

            # The queue_request() method creates the request and writes it to the send buffer. It also sets the state variable
            #   _request_queued so that it¡¯s only called once.
            self.queue_request()

        # The ._write() calls socket.send() if there¡¯s data in the send buffer.
        self._write()

        # The reason for this is to tell selector.select() to stop monitoring the socket for write events. If the request 
        #   has been queued and the send buffer is empty, then you¡¯re done writing and you¡¯re only interested in read events
        if self._request_queued:
            if not self._send_buffer:
                
                # Set selector to listen for read events, we're done writing.
                self._set_selector_events_mask("r")

        