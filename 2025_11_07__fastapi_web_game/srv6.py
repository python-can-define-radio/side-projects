"""to run:   fastapi dev srv5.py"""
import asyncio
import random
import string
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from rx.subject import Subject
from rx import operators as ops

from srv6_helper import GameState, CliEvent, Disconnect


app = FastAPI()

    
class GSMgr:
    """Game state manager"""
    def __init__(self):
        self.__gs = GameState()
        
    def relay_cli_msg(self, cm: CliEvent) -> str:
        return self.__gs.process_cli_msg(cm)

class ConnMgr:
    def __init__(self):
        self.__incoming = Subject()
        self.__gsm = GSMgr()
        self.__proc = self.__incoming.pipe(ops.map(self.__gsm.relay_cli_msg))

    def ws_rx(self, websocket):
        """Create connections between websockets and rxpy.  
        Returns `(put, disposable)`.
         - `put`: should call this on incoming messages
         - `dispose`: should call this when the connection is complete
        
        # Demo:
        # Setup note: this will use a fake websocket that will print instead of sending.
        # >>> class FakeWS:
        # ...     async def send_text(x):
        # ...         print(x)
        # >>> cm = ConnMgr()
        # >>> put, dispose = cm.ws_rx(FakeWS)
        
        # When we `put` received data, rxpy handles it:
        # >>> put('{"x": 3, "y": 5}')
        # procmsg: id='...'; payload='pretend message'
        
        # Ensuring that dispose works:
        # >>> dispose()
        # >>> put("nothing should happen now")
        """
        def send(x):
            asyncio.create_task(websocket.send_text(x))
        cid = "".join(random.sample(string.ascii_lowercase, k=4))
        disposable = self.__proc.subscribe(on_next=send)
        def put(payload):
            if payload is None:
                ev = Disconnect(cid)
            else:
                ev = CliEvent(cid, payload)
            self.__incoming.on_next(ev)

        return put, disposable.dispose


async def game_loop():
    while True:
        await asyncio.sleep(0.03)  # ~33 FPS
        connmgr._ConnMgr__gsm._GSMgr__gs.tick()
        # broadcast the new state
        msg = connmgr._ConnMgr__gsm._GSMgr__gs.process_cli_msg(
            CliEvent("server", json.dumps({"eventkind": "noop"}))
        )
        # send to all subscribers
        connmgr._ConnMgr__incoming.on_next(CliEvent("server", json.dumps({"eventkind": "broadcast", "msg": msg})))


@app.on_event("startup")
async def on_startup():
    asyncio.create_task(game_loop())

connmgr = ConnMgr()


@app.get("/")
async def get():
    with open("cli6.html") as f:
        return HTMLResponse(f.read())
    

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    put, dispose = connmgr.ws_rx(websocket)
    try:
        while True:
            payload = await websocket.receive_text()
            put(payload)
    except WebSocketDisconnect:
        dispose()
        put(None)
    

if __name__ == "__main__":
    import doctest; doctest.testmod(optionflags=doctest.ELLIPSIS)
