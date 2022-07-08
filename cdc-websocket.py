import asyncio
import json
import hmac
import hashlib

import websockets
import requests

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

# asyncio.get_event_loop().run_until_complete(hello())

class CDC:
    def __init__(self, keys, sandbox=True):
        """Creates an instance of the CDC object.
        keys: a dictionary with two keys, 'api' and 'secret', with the key strings as values
        """
        self.secret = keys['secret']
        self.api_keys = keys['api']

        if sandbox:
            self.rest_endpoint = 'https://uat-api.3ona.co/v2/'
            self.websocket_market_endpoint = 'wss://uat-stream.3ona.co/v2/market'
            self.websocket_user_endpoint = 'wss://uat-stream.3ona.co/v2/user'
        else:
            self.rest_endpoint = 'https://api.crypto.com/v2/'
            self.websocket_market_endpoint = 'wss://stream.crypto.com/v2/market'
            self.websocket_user_endpoint = 'wss://stream.crypto.com/v2/user'

    def get_candlesticks(self, instrument_name, time_frame, depth):
        """Get candlesticks based on provided instrument_name and time_frame
        instrument_name: (str) the name of the instrument, e.g. BTC_USDC, or ETH_USDC, or ETH_BTC
        time_frame: (str) time frame of the candles; valid time frames: 1m, 5m, 15m, 30m, 1h, 4h, 6h, 12h, 1D, 7D, 14D, 1M
        depth: (int) the number of candles to return (i think the max is 1000)

        returns list of candlesticks
        """

        url = f'{self.rest_endpoint}public/get-candlestick?instrument_name={instrument_name}&timeframe={time_frame}&depth={str(depth)}'

        response = requests.get(url)
        response_text = response.text
        response_dict = json.loads(response_text)
        print(response_dict['result'])

if __name__ == '__main__':

    with open('keys.json', 'r') as f:
        keys = json.load(f)
    cdc = CDC(keys, sandbox=True)

    cdc.get_candlesticks('BTC_USDC', '1m', 10)