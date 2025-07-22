import asyncio
import json
import websockets
from websockets.exceptions import ConnectionClosedOK

rooms: dict[str, set[websockets.WebSocketServerProtocol]] = {}

async def handler(ws: websockets.WebSocketServerProtocol):
    room = ws.request.path.strip("/") or "lobby"
    rooms.setdefault(room, set()).add(ws)

    try:
        async for msg in ws:
            data     = json.loads(msg)
            username = data.get("username")
            message  = data.get("message")
            if not (username and message):
                continue

            out = json.dumps({
                "room": room,
                "username": username,
                "message": message
            })

            for client in rooms[room]:
                await client.send(out)

    except ConnectionClosedOK:
        pass
    finally:
        rooms[room].remove(ws)
        if not rooms[room]:
            del rooms[room]

async def main():
    async with websockets.serve(handler, "0.0.0.0", 6789):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
