import doctest
import socket
import time
from threading import Thread
from __future__ import annotations


class UserError(Exception):
    ...


def handle_asn():
    return "TODO"

  
def parse_sub_msg(msg: str) -> tuple[str, str]:
    """
    >>> r = parse_sub_msg('''sub
    ...  # Name: Bob
    ...  and the rest''')
    >>> r
    ('Bob', '# Name: Bob...and the rest')
    """
    assert msg.startswith("sub")
    msg_no_sub = msg[3:]
    cstrp = msg_no_sub.strip()
    firstline = cstrp.splitlines()[0]
    if firstline.lower().startswith("# name: "):
        name = firstline[8:]
        return name, cstrp
    else:
        print(f"Rejected because the beginning was {msg[:30]}")
        raise UserError("Must put name")


def handle_sub(msg: str) -> str:
    name, stucode = parse_sub_msg(msg)        
    outfile = open("student_data/" + name + ".py", "x")
    outfile.write(stucode)
    outfile.close()
    return f"Received {msg}"


def handle_grd(msg):
    return "TODO"


def handle_message_maythrow(msg: str) -> str:
    if msg.startswith("asn"):
        return handle_asn()
    elif msg.startswith("sub"):
        return handle_sub(msg)
    elif msg.startswith("grd"):
        return handle_grd(msg)
    else:
        return (
            "Commands you can send:\n"
            "?            : Displays this help message.\n"
            "asn          : Shows the currently available assignment.\n"
            "sub          : Submit an assignment. Type 'sub' for usage details.\n"
            "grd          : Shows graded assignments. Type 'grd' for usage details.\n"
        )


def handle_message(msg: str) -> bytes:
    try:
        return handle_message_maythrow(msg).encode("utf8")
    except UserError as e:
        return str(e).encode("utf8")
    except Exception as e:
        print("Exception: ", e)
        return b"Internal server error."


def handle_client(conn, addr):
    print('Connected by', addr, 'and ready to receive')
    msg = conn.recv(4096).decode("utf8")
    resp = handle_message(msg)
    conn.send(resp)
    time.sleep(0.1)  # Trying to let the client close the connection first, but eventually we have to close
    conn.close()


def accept_connections(s: socket.socket):
    while True:
        conn, addr = s.accept()
        t = Thread(target=lambda: handle_client(conn, addr))
        t.start()
        

def main():
    HOST = ''
    PORT = 50007              # Arbitrary non-privileged port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(1)
        print("Listening...")
        accept_connections(s)


if __name__ == "__main__":
    doctest.testmod() 
    main()
