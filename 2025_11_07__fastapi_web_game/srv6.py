"""to run:   fastapi dev srv5.py


Doctests:

>>> def fake_websocket_send(x):
...     print("send:", x)

Initial `ws_setup` call sends the static files to the client:
>>> cm = _ConnMgr(debug=True)
>>> proc, discon = cm.ws_setup(fake_websocket_send, verbose=True)
send: {"static": {}}

When the client sends an event, we process it:
>>> proc('{"eventkind": "init", "name": "abc", "shape": "circle", "color": "green"}')
proc: CliEvent(cid='...', payload_raw='{"eventkind": "init"...}')

Ticks send data to the client:
>>> cm.trigger_tick()
send: {"dynamic": {...}, "players": {"...": {"x": ..., "y": ...}}}

We eventually disconnect:
>>> discon()
proc: Disconnect(cid='...')
I: Removing ... from dict

After disconnecting, ticks no longer send data to that client:
>>> cm.trigger_tick()

---------

>>> async def fake_websocket_recv():
...     return "words"

>>> _websocket_endpoint_impl(fake_websocket_send, fake_websocket_recv, 2)
asdf
"""


import asyncio
from contextlib import asynccontextmanager
import random
import string
from typing import Callable

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from rx.subject import Subject

from srv6_helper import GameState, CliEvent, Disconnect



@asynccontextmanager
async def _lifespan(app: FastAPI):
    async def game_loop():
        fps = 30
        while True:
            await asyncio.sleep(1 / fps)
            _connmgr.trigger_tick()
    asyncio.create_task(game_loop())
    yield


class _ConnMgr:
    def __init__(self, debug=False):
        """`debug` is passed to GameState init"""
        self.__gs = GameState(debug=debug)
        self.__tickresult = Subject()
        """Used to pass data to clients on each frame/tick"""

    def trigger_tick(self):
        """Notify all subscribers of the latest game state computed by `.tick()`"""
        r = self.__gs.tick()
        self.__tickresult.on_next(r)

    def ws_setup(self, websocket_send: Callable, verbose=False):
        """Create connections between the `websocket` and rxpy, and send GameState static entities to the client.  
        Returns `(proc, discon)`:
        - `proc`: should call this on incoming messages from the client
        - `discon`: should call this when the connection is complete
        Demo in module docstring/doctest.
        """
        
        def proc(payload):
            """process the payload. Pass `None` when client disconnects."""
            if payload is None:
                ev = Disconnect(cid)
            else:
                ev = CliEvent(cid, payload)
            if verbose:
                print("proc:", ev)
            self.__gs.process_cli_msg(ev)

        def discon():
            """Tell the GameState that this client disconnected, and dispose the tick subscribe resources."""
            proc(None)
            disposable_tick.dispose()

        websocket_send(self.__gs.get_static())
        cid = "".join(random.sample(string.ascii_lowercase, k=4))
        disposable_tick = self.__tickresult.subscribe(on_next=websocket_send)
        return proc, discon


_connmgr = _ConnMgr()
app = FastAPI(lifespan=_lifespan)
app.mount("/assets", StaticFiles(directory="assets"), name="assets")


@app.get("/")
async def gethome():
    with open("cli6.html") as f:
        return HTMLResponse(f.read())
    

async def _websocket_endpoint_impl(websocket_send, websocket_recv, max_rcv_msgs = int(10e9)):
    """Setup using `ws_setup`, then repeatedly `websocket_recv` from this client until the client disconnects or `max_rcv_msgs` is reached. To receive for a long time, set `max_rcv_msgs` arbitrarily high.
    
    Ultimately close the connection if any of these occur:
    - the client disconnects (`WebSocketDisconnect` is raised)
    - `max_rcv_msgs` is reached
    - Any other exception is raised (these exceptions are intentionally not caught)
    """
    proc, discon = _connmgr.ws_setup(websocket_send)
    try:
        for _i in range(max_rcv_msgs):
            proc(await websocket_recv())
    except WebSocketDisconnect:
        pass 
    finally:
        discon()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    def send(x):
        asyncio.create_task(websocket.send_text(x))
    def recv():
        return websocket.receive_text()
    await _websocket_endpoint_impl(send, recv, 10)


if __name__ == "__main__":
    import doctest; doctest.testmod(optionflags=doctest.ELLIPSIS)
