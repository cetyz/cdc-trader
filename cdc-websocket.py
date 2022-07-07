import asyncio
import websockets
import json

request = json.dumps({
    'method': 'subscribe',
    'params': {
        'channels': ['trade.BTC_USDC']
    }
}
)


async def hello():
    async with websockets.connect('wss://stream.crypto.com/v2/market') as websocket:
        
        await websocket.send(request)

        while True:

            response = await websocket.recv()
            print(response)

asyncio.get_event_loop().run_until_complete(hello())