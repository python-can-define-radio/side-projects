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


class ConnMgr:
    def __init__(self):
        self.__gs = GameState()
        """Used to receive events from clients"""
        self.__tick = Subject()
        """Used to pass data to clients on each frame"""
        self.__tickdone = self.__tick.pipe(ops.map(lambda x: self.__gs.tick()))
        """Post-tick state... there's definitely a better way to do this."""

    def trigger_tick(self):
        self.__tick.on_next(None)

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
        disposable_tick = self.__tickdone.subscribe(on_next=send)
        def put(payload):
            if payload is None:
                ev = Disconnect(cid)
            else:
                ev = CliEvent(cid, payload)
            self.__gs.process_cli_msg(ev)

        def dispo():
            disposable_tick.dispose()
        return put, dispo


async def game_loop():
    fps = 30
    while True:
        await asyncio.sleep(1 / fps)
        connmgr.trigger_tick()


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
