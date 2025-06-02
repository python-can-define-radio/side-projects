from __future__ import annotations
import doctest
from pathlib import Path
import socket
import time
from threading import Thread


class UserError(Exception):
    ...


def writefile(fn: str, content: str, dry_run: bool):
    path = Path(fn)
    if dry_run:
        print("Writing to '{fn}' this content:")
        print(content)
    else:
        outfile = open(path, "x", encoding="utf8")
        outfile.write(stucode)
        outfile.close()


def handle_asn() -> str:
    return Path("./pe.txt").read_text()

  
def parse_sub_msg(msg: str) -> tuple[str, str]:
    """
    >>> r = parse_sub_msg('''sub
    ...  # Name: Bob
    ...  and the rest''')
    >>> r
    ('Bob', '# Name: Bob\\n and the rest')
    >>> try:
    ...     parse_sub_msg('sub words')
    ... except Exception as e:
    ...     print("Exception:", e)
    Rejected because the beginning was 'sub words'
    Exception: Must put name
    """
    assert msg.startswith("sub")
    msg_no_sub = msg[3:]
    cstrp = msg_no_sub.strip()
    firstline = cstrp.splitlines()[0]
    if firstline.lower().startswith("# name: "):
        name = firstline[8:]
        return name, cstrp
    else:
        print(f"Rejected because the beginning was {repr(msg[:30])}")
        raise UserError("Must put name on the first line of your submission using this format: # Name: Smith")


def handle_sub(msg: str, dry_run: bool) -> str:
    """
    >>> handle_sub('''sub
    ...  # name: joe
    ...  more things
    ...  ''',
    ...  dry_run=True)
    fix this doctest
    """
    assert msg.startswith("sub")
    name, stucode = parse_sub_msg(msg)        
    writefile("student_data/" + name + ".py", stucode, dry_run)
    return f"Received {msg}"


def handle_grd(msg):
    return "TODO"


def handle_message_maythrow(msg: str, dry_run: bool) -> str:
    """Choose action based on `msg`."""
    if msg.startswith("asn"):
        return handle_asn()
    elif msg.startswith("sub"):
        return handle_sub(msg, dry_run)
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


def handle_message(msg: str, dry_run: bool = False) -> bytes:
    """Runs `handle_message_maythrow` with a try/except wrapper."""
    try:
        return handle_message_maythrow(msg).encode("utf8")
    except UserError as e:
        return str(e).encode("utf8")
    except Exception as e:
        print("Exception: ", e)
        return b"Internal server error."


def recv_till_done(conn: socket.socket) -> bytes:
    """run `conn.recv` repeatedly."""
    result = b""
    while True:
        partialresult = conn.recv(1024)
        if partialresult:
            result += partialresult
        else:
            break
    return result


def handle_client(conn: socket.socket, addr):
    """Receive data from the client. Take appropriate action. Send response to client. Close connection."""
    print('Connected by', addr, 'and ready to receive')
    msg = recv_till_done(conn).decode("utf8")
    resp = handle_message(msg)
    conn.send(resp)
    time.sleep(0.1)  # Trying to let the client close the connection first, but eventually we have to close
    conn.close()
    print("Connection done with", addr)


def accept_connections(s: socket.socket):
    """Launch a thread to handle each client that connects."""
    while True:
        conn, addr = s.accept()
        t = Thread(target=lambda: handle_client(conn, addr))
        t.start()
        

def main():
    """Launch the server."""
    HOST = ''
    PORT = 7233              # Arbitrary non-privileged port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(1)
        print("Listening...")
        accept_connections(s)


if __name__ == "__main__":
    doctest.testmod() 
    main()
