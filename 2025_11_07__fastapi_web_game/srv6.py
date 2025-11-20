"""
To run:
    fastapi dev srv5.py

Summary:
1. serves the homepage (`gethome()`)
2. starts a game loop (`_lifespan()` and `game_loop()`)
3. handles websocket connection (`websocket_endpoint()` and others)

Game loop
---------

`game_loop` calls `trigger_tick` `_fps` times per second.
The current frames per second:
>>> _fps
30

`game_loop` is started as soon as the FastAPI app launches, but
it does very little until a client connects.

The following doctests demonstrate a connection.  
We'll trigger ticks manually in this demo rather than 
using the `game_loop`.

We'll also use print instead of a real websocket:
>>> def fake_websocket_send(x):
...     print("send:", x)

First, we create a Connection Manager (`_ConnMgr`) to handle all clients.
>>> cm = _ConnMgr(debug=True)

When a new client joins, `ws_setup` is called once.  
It immediately sends the static entities to that client:
>>> proc, discon = cm.ws_setup(fake_websocket_send, verbose=True)
send: {"static": {}}

The dynamic entities and players are sent on each tick.
Ticks also change the game state and send data to the client.
In this doctest session, there are currently no players.
>>> cm.trigger_tick()
send: {"dynamic": {}, "players": {}}

When the client sends an event, we process it using `proc`.
In this case, we are pretending that the client is sending
an "init" event, which it should send once upon joining.
>>> pretend_client_event = '{"eventkind": "init", "name": "abc", "avatar": "/assets/somefile.png"}'
>>> proc(pretend_client_event)
proc: CliEvent(cid='...', payload_raw='{"eventkind": "init"...}')

The game state will reflect that a client has joined, because
the `players` dict now has an element:
>>> cm.trigger_tick()
send: {"dynamic": {}, "players": {"...": {"x": ..., "y": ...}}}

We eventually disconnect:
>>> discon()
proc: Disconnect(cid='...')
I: Removing ... from dict

After disconnecting, ticks no longer send data to that client:
>>> cm.trigger_tick()

---------

In the current implementation, `ws_setup` (shown above) is only
called in `websocket_endpoint_impl`. Here's a demo doctest:

>>> async def async_fake_websocket_send(x):
...     print("async send:", x)

>>> async def async_fake_websocket_recv():
...     return '{"eventkind": "init", "name": "abc", "avatar": "/assets/somefile.png"}'

In the example below, the removal appears to be happening before the intial send.
Someday we may figure out how to avoid this race condition, but for now, it's probably
ok because most players aren't going to exit the game immediately after connecting.
>>> asyncio.run(cm.websocket_endpoint_impl(async_fake_websocket_send, async_fake_websocket_recv, max_rcv_msgs=2))
I: Removing ... from dict
async send: {"static": {}}
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
        while True:
            await asyncio.sleep(1 / _fps)
            _connmgr.trigger_tick()
    asyncio.create_task(game_loop())
    yield


class _ConnMgr:
    def __init__(self, debug=False):
        """`debug` is passed to GameState init"""
        self.__gs = GameState(create_entities=not debug)
        self.__tickresult = Subject()
        """Used to pass data to clients on each frame/tick"""

    def trigger_tick(self):
        """Notify all subscribers of the latest game state computed by `.tick()`.
        If the result of a tick is empty (no change), then don't notify subscribers."""
        r = self.__gs.tick()
        if r != "{}":
            self.__tickresult.on_next(r)

    def ws_setup(self, websocket_send_sync: Callable, verbose=False):
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
            disposable_tick.dispose()
            proc(None)

        websocket_send_sync(self.__gs.get_static())
        cid = "".join(random.sample(string.ascii_lowercase, k=10))
        disposable_tick = self.__tickresult.subscribe(on_next=websocket_send_sync)
        return proc, discon

    async def websocket_endpoint_impl(self, websocket_send, websocket_recv, max_rcv_msgs = int(10e9)):
        """Setup using `ws_setup`, then repeatedly call `websocket_recv` to receive from this client until the client disconnects or `max_rcv_msgs` is reached. To receive for a long time, set `max_rcv_msgs` arbitrarily high.
        
        Ultimately close the connection if any of these occur:
        - the client disconnects (`WebSocketDisconnect` is raised)
        - `max_rcv_msgs` is reached
        - Any other exception is raised (these exceptions are intentionally not caught)
        """
        def send_sync(x):
            asyncio.create_task(websocket_send(x))
        proc, discon = self.ws_setup(send_sync)
        try:
            for _i in range(max_rcv_msgs):
                proc(await websocket_recv())
        except WebSocketDisconnect:
            pass 
        finally:
            discon()


_connmgr = _ConnMgr()
_fps = 30
app = FastAPI(lifespan=_lifespan)
app.mount("/assets", StaticFiles(directory="assets"), name="assets")


@app.get("/")
async def gethome():
    with open("cli6.html") as f:
        return HTMLResponse(f.read())


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await _connmgr.websocket_endpoint_impl(websocket.send_text, websocket.receive_text)


if __name__ == "__main__":
    import doctest; doctest.testmod(optionflags=doctest.ELLIPSIS)
