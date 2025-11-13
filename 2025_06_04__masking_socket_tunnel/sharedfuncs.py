import socket
import time
from threading import Thread



def masking_message_handler(msg: bytes, ipaddr: str, port: int):
    """Masks `msg` andn sends to `ipaddr` on specified `port`. Returns server reply."""
    masked = b"mask" + msg
    print(f"handling the msg {masked}")
    server_said = connect_tx_rx_close(ipaddr, port, masked, 4.0)
    print("the server's proxy said", server_said)
    return server_said


def unmasking_message_handler(msg: bytes, ipaddr: str, port: int):
    """Masks `msg` andn sends to `ipaddr` on specified `port`. Returns server reply."""
    if not msg.startswith(b"mask"):
        raise ValueError(f"Cannot unmask. Message should start with 'mask', but starts with {msg[:10]}")
    unmasked = msg[4:]
    print(f"handling the msg {unmasked}")
    server_said = connect_tx_rx_close(ipaddr, port, unmasked, 0.5)
    print("the final http server said", server_said)
    masked_server_reply = b"mask" + server_said
    return masked_server_reply


def receive_until_timeout(conn, seconds: float) -> bytes:
    """receive repeatedly until `seconds` seconds have passed since the last message.
    `conn` can either be a socket.socket (for real use) or anything with a .recv() and
    a .settimeout() (for testing).
    """
    # This function is very ugly implementation and should be improved.
    conn.settimeout(0)
    totmsg = b""
    dela = 0.1
    max_sleeps = int(seconds / 0.1)
    sleeps = 0
    while True:
        try:
            msgpiece = conn.recv(1024)
            if msgpiece:
                print("Got a piece of length", len(msgpiece))
                sleeps = 0
                totmsg += msgpiece
            else:  # other end disconnected
                sleeps = 99999  # arbitrarily large number
        except BlockingIOError:
            time.sleep(dela)
            sleeps += 1
        except Exception as e:
            raise
        if sleeps > max_sleeps:
            return totmsg


def connect_tx_rx_close(ipaddr: str, port: int, tosend: bytes, timeout_seconds: float) -> bytes:
    """Sends all of `tosend` to the specified ip address and port.
    Receives and returns all data that is available in 2 seconds."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ipaddr, port))
    s.sendall(tosend)
    recvd = receive_until_timeout(s, timeout_seconds)
    s.close()
    return recvd


def handle_client(conn: socket.socket, addr, message_handler, timeout_seconds, next_step_addr, next_step_port):
    """Receive data from the client. Take appropriate action. Send response to client. Close connection."""
    print('Connected by', addr, 'and ready to receive')
    msg = receive_until_timeout(conn, timeout_seconds)
    resp = message_handler(msg, next_step_addr, next_step_port)
    conn.sendall(resp)
    time.sleep(4.0)  # Trying to let the client close the connection first
    conn.close()
    print("Connection done with", addr)


def accept_connections(s: socket.socket, message_handler, timeout_seconds, next_step_addr, next_step_port):
    """Launch a thread to handle each client that connects."""
    while True:
        conn, addr = s.accept()
        t = Thread(target=lambda: handle_client(conn, addr, message_handler, timeout_seconds, next_step_addr, next_step_port))
        t.start()
            

def launch_server(port: int, message_handler, timeout_seconds, next_step_addr, next_step_port):
    """Bind, listen, run `accept_connections`."""
    HOST = ''
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, port))
        s.listen(1)
        print(f"Listening on port {port}...")
        accept_connections(s, message_handler, timeout_seconds, next_step_addr, next_step_port)


if __name__ == "__main__":
    doctest.testmod(optionflags=doctest.ELLIPSIS) 
