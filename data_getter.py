import asyncio
import json
import hmac
import hashlib
import time
import csv
import os

import websockets
import requests

DATA_FILE_NAME = 'data3.csv'



request = json.dumps({
    'method': 'subscribe',
    'params': {
        'channels': [
            'candlestick.5m.BTC_USDC',
            'candlestick.5m.ETH_USDC',
            'candlestick.5m.ETH_BTC'
        ]
    }
}
)
def build_heartbeat(id):
    body = {
        'id': id,
        'method': 'public/respond-heartbeat'
    }
    return(json.dumps(body))


async def hello():
    async with websockets.connect('wss://stream.crypto.com/v2/market') as websocket:
        
        await websocket.send(request)

        while True:

            response = await websocket.recv()
            response_json = json.loads(response)

            if response_json['method'] == 'public/heartbeat':
                await websocket.send(build_heartbeat(id=response_json['id']))

            elif (response_json['method'] == 'subscribe') and ('result' in response_json.keys()):
                instrument = response_json['result']['instrument_name']
                data_dict = response_json['result']['data'][0]
                # data_dict = json.loads(data_dict)

                to_write = []
                to_write.append(instrument)
                to_write.append(data_dict['t'])
                to_write.append(data_dict['o'])
                to_write.append(data_dict['h'])
                to_write.append(data_dict['l'])
                to_write.append(data_dict['c'])
                to_write.append(data_dict['v'])
                
                if DATA_FILE_NAME not in os.listdir():
                    try:
                        with open(DATA_FILE_NAME, 'w') as f:
                            writer = csv.writer(f)
                            writer.writerow(['instrument', 't', 'o', 'h', 'l', 'c', 'v'])
                    except:
                        pass

                try:
                    with open(DATA_FILE_NAME, 'a') as f:
                        writer = csv.writer(f)
                        writer.writerow(to_write)
                except:
                    pass

                print(to_write)
while True:
    try:

        asyncio.get_event_loop().run_until_complete(hello())

    except:

        print('exception occured, trying again')
