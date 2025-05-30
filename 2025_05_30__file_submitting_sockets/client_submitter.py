import socket


def connect_tx_rx_close(tosend: str) -> str:
    HOST = '10.50.129.202'
    PORT = 7233
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.send(tosend.encode("utf8"))
    recvd = s.recv(1024).decode("utf8")
    s.close()
    return recvd

# Change `sendthis` to whatever command you want to run
sendthis = "?"
serversaid = connect_tx_rx_close(sendthis)
print("Server's reply:", serversaid)

