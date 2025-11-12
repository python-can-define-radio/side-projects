from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import random
import json

app = FastAPI()
clients = {}

def random_color():
    return f"rgb({random.randint(0,255)}, {random.randint(0,255)}, {random.randint(0,255)})"

def random_position():
    return {"x": random.randint(0,800), "y": random.randint(0,400)}

@app.get("/")
async def get():
    with open("cli2.html") as f:
        return HTMLResponse(f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    player_id = id(websocket)
    clients[player_id] = {
        "socket": websocket,
        "color": random_color(),
        "position": random_position()
    }

    # Send initial state to new player
    await websocket.send_text(json.dumps({
        "type": "init",
        "player_id": player_id,
        "color": clients[player_id]["color"],
        "position": clients[player_id]["position"]
    }))

    # Send existing players to the new client
    for pid, client in clients.items():
        if pid != player_id:
            await websocket.send_text(json.dumps({
                "type": "new_player",
                "player_id": pid,
                "color": client["color"],
                "position": client["position"]
            }))


    # Broadcast new player to others
    for pid, client in clients.items():
        if pid != player_id:
            await client["socket"].send_text(json.dumps({
                "type": "new_player",
                "player_id": player_id,
                "color": clients[player_id]["color"],
                "position": clients[player_id]["position"]
            }))

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg["type"] == "move":
                clients[player_id]["position"] = msg["position"]
                # Broadcast updated position
                for pid, client in clients.items():
                    await client["socket"].send_text(json.dumps({
                        "type": "update",
                        "player_id": player_id,
                        "position": msg["position"]
                    }))
    except WebSocketDisconnect:
        del clients[player_id]
        # Notify others of disconnect
        for pid, client in clients.items():
            await client["socket"].send_text(json.dumps({
                "type": "remove",
                "player_id": player_id
            }))
