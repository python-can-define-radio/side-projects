"""to run:   fastapi dev srv5.py"""
import asyncio
from contextlib import asynccontextmanager
import random
import string
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from rx.subject import Subject
from rx import operators as ops

from srv6_helper import GameState, CliEvent, Disconnect



@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(game_loop())
    yield


app = FastAPI(lifespan=lifespan)



app = FastAPI()

app.mount("/assets", StaticFiles(directory="assets"), name="assets")

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

    def ws_rx(self, websocket, verbose=False):
        """Create connections between websockets and rxpy.  
        Returns `(put, discon)`.
         - `put`: should call this on incoming messages
         - `discon`: should call this when the connection is complete
        
        Demo:
        Setup note: this will use a fake websocket that will print instead of sending.
        >>> class FakeWS:
        ...     async def send_text(x):
        ...         print(x)
        >>> cm = ConnMgr()
        >>> put, discon = cm.ws_rx(FakeWS, verbose=True)
        
        When we `put` received data, something happens:
        >>> put('{"eventkind": "init", "name": "abc", "shape": "circle", "color": "green"}')
        put: CliEvent(cid='aeid', payload_raw='...')

        >>> cm.trigger_tick()
        todo
        
        >>> discon()
        disconnecting.
        """
        def send(x):
            asyncio.create_task(websocket.send_text(x))
        
        def put(payload):
            """put either the payload or `None` for disconnect"""
            if payload is None:
                ev = Disconnect(cid)
            else:
                ev = CliEvent(cid, payload)
            if verbose:
                print("put:", ev)
            self.__gs.process_cli_msg(ev)

        def discon():
            if verbose:
                print("disconnecting.")
            put(None)
            disposable_tick.dispose()

        cid = "".join(random.sample(string.ascii_lowercase, k=4))
        disposable_tick = self.__tickdone.subscribe(on_next=send)
        return put, discon


async def game_loop():
    fps = 30
    while True:
        await asyncio.sleep(1 / fps)
        connmgr.trigger_tick()


connmgr = ConnMgr()


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
