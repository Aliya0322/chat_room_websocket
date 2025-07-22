import asyncio
import json
import websockets
from websockets import broadcast
from websockets.exceptions import ConnectionClosedOK

auctions: dict[str, dict] = {}

async def auction_timer(lot_id: str):
    while True:
        info = auctions.get(lot_id)
        if not info:
            return
        if info["remaining"] <= 0:
            winner = info["leader"]
            amount = info["amount"]
            msg = json.dumps({"event": "auction_closed", "winner": winner, "final_amount": amount})
            broadcast(info["clients"], msg)
            del auctions[lot_id]
            return
        info["remaining"] -= 1
        timer_msg = json.dumps({"event": "timer", "remaining_seconds": info["remaining"]})
        broadcast(info["clients"], timer_msg)
        await asyncio.sleep(1)

async def handler(ws: websockets.WebSocketServerProtocol):
    path = ws.request.path
    lot_id = path.strip("/").split("/")[-1] or "default"
    if lot_id not in auctions:
        auctions[lot_id] = {
            "clients": set(),
            "leader": None,
            "amount": 0,
            "remaining": 120,
        }
        auctions[lot_id]["timer_task"] = asyncio.create_task(auction_timer(lot_id))

    info = auctions[lot_id]
    info["clients"].add(ws)

    init = json.dumps({
        "event": "init",
        "leader": info["leader"],
        "amount": info["amount"],
        "remaining_seconds": info["remaining"]
    })
    await ws.send(init)

    try:
        async for msg in ws:
            data = json.loads(msg)
            bidder = data.get("bidder")
            bid = data.get("amount")
            if info["remaining"] <= 0:
                await ws.send(json.dumps({"event": "bid_rejected", "reason": "Аукцион закрыт"}))
            elif not bidder or not isinstance(bid, (int, float)):
                await ws.send(json.dumps({"event": "bid_rejected", "reason": "Неверный формат ставки"}))
            elif bid <= info["amount"]:
                await ws.send(json.dumps({"event": "bid_rejected", "reason": "Ставка меньше текущей"}))
            else:
                info["leader"] = bidder
                info["amount"] = bid
                broadcast(info["clients"], json.dumps({"event": "bid_accepted", "bidder": bidder, "amount": bid}))
    except ConnectionClosedOK:
        pass
    finally:
        info["clients"].remove(ws)
        if not info["clients"] and info["remaining"] <= 0:
            task = info.get("timer_task")
            if task:
                task.cancel()
            auctions.pop(lot_id, None)

async def main():
    async with websockets.serve(handler, "0.0.0.0", 6789):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
