"""to run:   fastapi dev srv5.py"""
import asyncio
from contextlib import asynccontextmanager
import random
import string
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from rx.subject import Subject

from srv6_helper import GameState, CliEvent, Disconnect



@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(game_loop())
    yield


class ConnMgr:
    def __init__(self):
        self.__gs = GameState()
        self.__tickresult = Subject()
        """Used to pass data to clients on each frame"""

    def trigger_tick(self):
        """Notify all subscribers of the latest game state computed by `.tick()`"""
        r = self.__gs.tick()
        self.__tickresult.on_next(r)

    def ws_rx(self, websocket, debug=False):
        """Create connections between websockets and rxpy.  
        Returns `(put, discon)`.
         - `put`: should call this on incoming messages
         - `discon`: should call this when the connection is complete
        
        Demo:
        >>> cm = ConnMgr()
        >>> put, discon = cm.ws_rx(None, debug=True)
        
        When we `put` received data, something happens:
        >>> put('{"eventkind": "init", "name": "abc", "shape": "circle", "color": "green"}')
        put: CliEvent(cid='...', payload_raw='...')

        >>> cm.trigger_tick()
        send: {"entities": ..., "players": ...}
        
        >>> discon()
        put: Disconnect(cid='...')
        I: Removing ... from dict
        """
        def send(x):
            if debug:
                print("send:", x)
            else:
                asyncio.create_task(websocket.send_text(x))
        
        def put(payload):
            """put either the payload or `None` for disconnect"""
            if payload is None:
                ev = Disconnect(cid)
            else:
                ev = CliEvent(cid, payload)
            if debug:
                print("put:", ev)
            self.__gs.process_cli_msg(ev)

        def discon():
            """Tell the GameState that this client disconnected, and dispose the tick subscribe resources."""
            put(None)
            disposable_tick.dispose()

        cid = "".join(random.sample(string.ascii_lowercase, k=4))
        disposable_tick = self.__tickresult.subscribe(on_next=send)
        return put, discon


async def game_loop():
    fps = 30
    while True:
        await asyncio.sleep(1 / fps)
        connmgr.trigger_tick()


connmgr = ConnMgr()
app = FastAPI(lifespan=lifespan)
app.mount("/assets", StaticFiles(directory="assets"), name="assets")


@app.get("/")
async def get():
    with open("cli6.html") as f:
        return HTMLResponse(f.read())
    

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    put, discon = connmgr.ws_rx(websocket)
    try:
        while True:
            payload = await websocket.receive_text()
            put(payload)
    except WebSocketDisconnect:
        discon()


if __name__ == "__main__":
    import doctest; doctest.testmod(optionflags=doctest.ELLIPSIS)
