from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from srv3_helpers import make_rx_send_stream
import asyncio
from rx.scheduler.eventloop import AsyncIOScheduler



app = FastAPI()
connected_clients = {}


@app.get("/")
async def get():
    with open("cli3.html") as f:
        return HTMLResponse(f.read())


async def broadcast(pos):
    for websocket in connected_clients.copy():
        try:
            await websocket.send_json(pos)
        except WebSocketDisconnect:
            handle_disconnect(websocket)


def handle_disconnect(websocket):
    disposable = connected_clients[websocket]
    disposable.dispose()
    del connected_clients[websocket]
    print(connected_clients)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    loop = asyncio.get_event_loop()
    scheduler = AsyncIOScheduler(loop=loop)

    disposable = make_rx_send_stream().subscribe(
        on_next=lambda pos: asyncio.create_task(broadcast(pos)),
        scheduler=scheduler
    )

    connected_clients[websocket] = disposable

    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        handle_disconnect(websocket)
