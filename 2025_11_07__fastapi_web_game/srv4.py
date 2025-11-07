from typing import NamedTuple
import random
import string
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from rx.subject import Subject
from rx import operators as ops


app = FastAPI()


class CliMsg(NamedTuple):
    """A message from a client"""
    cid: str
    payload: str


def process_cli_msg(cm: CliMsg):
    return f"procmsg: id={repr(cm.cid)}; payload={repr(cm.payload)}"


class GlobalState:
    def __init__(self):
        self.__incoming = Subject()
        self.__proc = self.__incoming.pipe(ops.map(process_cli_msg))

    def ws_rx(self, websocket):
        """Create connections between websockets and rxpy.  
        Returns `(put, disposable)`.
         - `put`: should call this on incoming messages
         - `dispose`: should call this when the connection is complete
        
        Demo:
        Setup note: this will use a fake websocket that will print instead of sending.
        >>> class FakeWS: send_text = print
        >>> gs = GlobalState()
        >>> put, dispose = gs.ws_rx(FakeWS)
        
        When we `put` received data, rxpy handles it:
        >>> put("pretend message")
        procmsg: id='...'; payload='pretend message'
        
        Ensuring that dispose works:
        >>> dispose()
        >>> put("nothing should happen now")
        """
        cid = "".join(random.sample(string.ascii_lowercase, k=4))
        disposable = self.__proc.subscribe(on_next=websocket.send_text)
        def put(payload: str):
            self.__incoming.on_next(CliMsg(cid, payload))
        return put, disposable.dispose

globalstate = GlobalState()


@app.get("/")
async def get():
    with open("cli_clicker.html") as f:
        return HTMLResponse(f.read())
    

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    put, dispose = globalstate.ws_rx(websocket)
    try:
        while True:
            payload = await websocket.receive_text()
            put(payload)
    except WebSocketDisconnect:
        dispose()
    
