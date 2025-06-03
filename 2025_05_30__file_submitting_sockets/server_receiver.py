"""
A server that allows viewing and submitting assignments.
"""

from __future__ import annotations
import doctest
from pathlib import Path
import socket
import time
from threading import Thread
import os


class UserError(Exception):
    ...


def eq(a, b):
    if type(a) != type(b):
        raise TypeError("Tried to check whether {a} and {b} are equal, but they are not of the same type.")
    return a == b


def writefile(fn: str, content: str, dry_run: bool, mode: str = "x"):
    """If `dry_run` is False, write `content` to the file `fn`.  
    If `dry_run` is True, print the filename and what would be written.
    The `mode` arg is passed to Python's `open` function.

    >>> writefile("myfile.txt", "words", True)
    Dry run. Would write to 'myfile.txt' this content:
    words
    """
    path = Path(fn)
    if dry_run:
        print(f"Dry run. Would write to '{fn}' this content:")
        print(content)
    else:
        outfile = open(path, mode, encoding="utf8")
        outfile.write(content)
        outfile.close()


def handle_asn() -> str:
    """Return the active assignment."""
    try:
        return Path("./pe.txt").read_text()
    except FileNotFoundError:
        return "There is no current assignment."

  
def parse_sub_msg(msgarg: str) -> tuple[str, str]:
    """Given a correctly formatted msgarg, return the tuple `(name, content)`. 

    Example 1: result when the submission is correctly formatted
    >>> msg = '''
    ... # Name: Bob
    ... and the rest
    ... '''
    >>> name, content = parse_sub_msg(msg)
    >>> name
    'Bob'
    >>> print(content)
    # Name: Bob
    and the rest
    
    >>> try:
    ...     parse_sub_msg('sub words')
    ... except Exception as e:
    ...     print("Exception:", e)
    Rejected because the beginning was 'sub words'
    Exception: Submission example...
    """
    sub_example = (
        "Submission example:\n"
        "sub\n"
        "# Name: Smith\n"
        "# Code:\n"
        "your\n"
        "code\n"
        "goes\n"
        "here\n"
    )
    
    cstrp = msgarg.strip()
    firstline = cstrp.splitlines()[0]
    if firstline.lower().startswith("# name: "):
        name = firstline[8:]
        return name, cstrp
    else:
        print(f"Rejected because the beginning was {repr(msgarg[:30])}")
        raise UserError(sub_example)


def handle_sub(msgarg: str, dry_run: bool) -> str:
    """Given the message argument msgarg, either
    (a) save the student's submission to a file, or
    (b) give directions/error messages.

    >>> msgarg = '''
    ... # Name: joe
    ... more things
    ... '''
    >>> r = handle_sub(msgarg, dry_run=True)
    Dry run. Would write to 'student_data/joe.py' this content:
    # Name: joe
    more things
    >>> r
    'Received submission ...'
    """
    name, stucode = parse_sub_msg(msgarg)
    os.makedirs("student_data", exist_ok=True)
    writefile("student_data/" + name + ".py", stucode, dry_run)
    return f"Received submission {msgarg}"


def handle_grd(subargs):
    return "TODO"


def handle_message_maythrow(msg: str, dry_run: bool) -> str:
    """Choose action based on `msg` and return a status message.

    Example: student named "Bob" submits the following:
    >>> msg = '''
    ... sub
    ... # Name: Bob
    ... and more words
    ... '''
    >>> result = handle_message_maythrow(msg, dry_run=True)
    Dry run. Would write to 'student_data/Bob.py' this content:
    # Name: Bob
    and more words
    >>> result
    'Received submission...'

    Example: student wants to view the current quiz/assignment:
    >>> msg = 'asn'
    >>> result = handle_message_maythrow(msg, dry_run=True)
    >>> result
    'There is no current assignment.'

    Invalid messages will return a help message:
    >>> msg = "junk"
    >>> result = handle_message_maythrow(msg, dry_run=True)
    Command 'junk' not recognized.
    >>> print(result)
    You sent 'junk'.
    Commands you can send:...
    """
    def elem_or_emp(lst: "list[str]") -> str:
        """Return the single string contained in the list,
        or an empty string if the list is empty."""
        assert len(lst) < 2
        if lst == []:
            return ""
        return lst[0]
    
    strp = msg.strip()
    pieces = strp.split(maxsplit=1)
    cmd = pieces[0].strip()
    therest = pieces[1:]
    subarg = elem_or_emp(therest)
    
    if eq(cmd, "asn"):
        return handle_asn()
    elif eq(cmd, "sub"):
        return handle_sub(subarg, dry_run)
    elif eq(cmd, "grd"):
        return handle_grd(subarg)
    else:
        print(f"Command '{cmd}' not recognized.")
        return (
            f"You sent '{msg}'.\n"
            "Commands you can send:\n"
            "?            : Displays this help message.\n"
            "asn          : Shows the currently available assignment.\n"
            "sub          : Submit an assignment. Type 'sub' for usage details.\n"
            "grd          : Shows graded assignments. Type 'grd' for usage details.\n"
        )


def handle_message(msg: str, dry_run: bool = False) -> bytes:
    """Runs `handle_message_maythrow` with a try/except wrapper."""
    try:
        return handle_message_maythrow(msg, dry_run).encode("utf8")
    except UserError as e:
        return str(e).encode("utf8")
    except Exception as e:
        print("Exception: ", e)
        return b"Internal server error."


def handle_client(conn: socket.socket, addr):
    """Receive data from the client. Take appropriate action. Send response to client. Close connection."""
    print('Connected by', addr, 'and ready to receive')
    time.sleep(0.1) # Let client have time to send message. Eventually this should be based on a protocol in which the client says how long the message will be.
    msg =  conn.recv(4096).decode("utf8")
    resp = handle_message(msg)
    conn.send(resp)
    time.sleep(0.1)  # Trying to let the client close the connection first
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
    doctest.testmod(optionflags=doctest.ELLIPSIS) 
    # main()
