import asyncio
import json
import hmac
import hashlib
import time

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
    def __init__(self, api_key, secret_key, sandbox=True):
        """Creates an instance of the CDC object.
        keys: a dictionary with two keys, 'api' and 'secret', with the key strings as values
        """
        self.secret = secret_key
        self.api_key = api_key

        if sandbox:
            self.rest_endpoint = 'https://uat-api.3ona.co/exchange/v1/'
            self.websocket_market_endpoint = 'wss://uat-stream.3ona.co/exchange/v1/market'
            self.websocket_user_endpoint = 'wss://uat-stream.3ona.co/exchange/v1/user'
        else:
            self.rest_endpoint = 'https://api.crypto.com/exchange/v1/'
            self.websocket_market_endpoint = 'wss://stream.crypto.com/exchange/v1/market'
            self.websocket_user_endpoint = 'wss://stream.crypto.com/exchange/v1/user'


    def add_signature(self, req):
        """Adds digital signature to request.

        Args:
            req (dict): private request in dictionary form

        Returns:
            req (dict): same request that was entered but with additional signature as key
        """

        # First ensure the params are alphabeticall sorted by key
        param_str = ""

        MAX_LEVEL = 3
        
        def params_to_str(obj, level):
            if level >= MAX_LEVEL:
                return str(obj)
            
            return_str = ""
            for key in sorted(obj):
                return_str += key
                if obj[key] is None:
                    return_str += 'null'
                elif isinstance(obj[key], list):
                    for subObj in obj[key]:
                        return_str += params_to_str(subObj, level + 1)
                else:
                    return_str += str(obj[key])
            return return_str
        
        if "params" in req:
            param_str = params_to_str(req['params'], 0)

        payload_str = req['method'] + str(req['id']) + req['api_key'] + param_str + str(req['nonce'])

        req['sig'] = hmac.new(
            bytes(str(self.secret), 'utf-8'),
            msg=bytes(payload_str, 'utf-8'),
            digestmod=hashlib.sha256
        ).hexdigest()

        return(req)

    def get_instruments(self):

        url = f'{self.rest_endpoint}public/get-instruments'

        response = requests.get(url)
        response_text = response.text
        response_dict = json.loads(response_text)

        return(response_dict)


    def get_candlesticks(self, instrument_name, time_frame, count):
        """Get candlesticks based on provided instrument_name and time_frame
        instrument_name: (str) the name of the instrument, e.g. BTC_USDC, or ETH_USDC, or ETH_BTC
        time_frame: (str) time frame of the candles; valid time frames: 1m, 5m, 15m, 30m, 1h, 4h, 6h, 12h, 1D, 7D, 14D, 1M
        count: (int) the number of candles to return (i think the max is 300)

        returns list of candlesticks
        """

        url = f'{self.rest_endpoint}public/get-candlestick?instrument_name={instrument_name}&timeframe={time_frame}&count={str(count)}'

        response = requests.get(url)
        response_text = response.text
        response_dict = json.loads(response_text)

        return(response_dict['result']['data'])

    def create_market_order(self, instrument_name, side, quantity, stop_loss, take_profit):
        """Create a market order with stop loss and take profit.
        Creates stop loss and take profit OCO order first.
        If either fail to be created, all other orders will be cancelled just in case.

        Args:
            instrument_name (str): the name of the instrument, e.g. BTCUSD-PERP or ETHUSD-PERP
            side (str): 'BUY' or 'SELL'
            quantity (float): quantity of the trade
            stop_loss (float): stop loss price
            take_profit (float): take profit price
        """

        oco_nonce = int(time.time() * 1000)

        if side == 'BUY':
            oco_side = 'SELL'
        elif side == 'SELL':
            oco_side = 'BUY'

        oco_req = {
            'method': 'private/create-order-list',
            'id': 0,
            'nonce': oco_nonce,
            'api_key': self.api_key,
            'params': {
                'contingency_type': 'OCO',
                'order_list': [
                    {
                        'instrument_name': instrument_name,
                        'quantity': str(quantity),
                        'type': 'LIMIT',
                        'price': str(take_profit),
                        'side': oco_side
                    },
                    {
                        'instrument_name': instrument_name,
                        'quantity': str(quantity),
                        'type': 'STOP_LOSS',
                        'ref_price': str(stop_loss),
                        'side': oco_side
                    }
                ]
            }
        }

        oco_req = self.add_signature(oco_req)
        oco_response = requests.post(self.rest_endpoint+'private/create-order-list', json=oco_req, headers={'Content-Type': 'application/json'})
        if oco_response.status_code == 200:
            print('Stop Loss and Take Profit OCO order created successfully')
        oco_list_id = oco_response.json()['result']['list_id']

        time.sleep(3)

        oco_cancel_nonce = int(time.time() * 1000)

        oco_cancel_req = {
            'method': 'private/cancel-order-list',
            'id': 0,
            'nonce': oco_cancel_nonce,
            'api_key': self.api_key,
            'params': {
                'instrument_name': instrument_name,
                'list_id': str(oco_list_id),
                'contingency_type': 'OCO'
            }
        }

        oco_cancel_req = self.add_signature(oco_cancel_req)
        oco_cancel_response = requests.post(self.rest_endpoint+'private/cancel-order-list', json=oco_cancel_req, headers={'Content Type': 'application/json'})

        return oco_cancel_response.text


    def create_limit_order(self, instrument_name, side, price, quantity):
        """Create a LIMIT order
        instrument_name: (str) the name of the instrument, e.g. BTC_USDC, or ETH_USDC, or ETH_BTC
        side: (str) BUY or SELL
        price: (float) unit price
        quantity: (float) quantity for the trade

        returns confirmation of order creation
        """




        nonce = int(time.time() * 1000)
        req = {
            "id": 0,
            "method": "private/create-order",
            "api_key": self.api_key,
            "params": {
                'instrument_name': instrument_name,
                'side': side,
                'type': 'LIMIT',
                'price': price,
                'quantity': quantity,
                'time_in_force': 'GOOD_TILL_CANCEL',
            },
            "nonce": nonce
        }

        # First ensure the params are alphabetically sorted by key
        param_str = ""

        MAX_LEVEL = 3


        def params_to_str(obj, level):
            if level >= MAX_LEVEL:
                return str(obj)

            return_str = ""
            for key in sorted(obj):
                return_str += key
                if isinstance(obj[key], list):
                    for subObj in obj[key]:
                        return_str += params_to_str(subObj, ++level)
                else:
                    return_str += str(obj[key])
            return return_str


        if "params" in req:
            param_str = params_to_str(req['params'], 0)

        payload_str = req['method'] + str(req['id']) + req['api_key'] + param_str + str(req['nonce'])

        req['sig'] = hmac.new(
            bytes(str(self.secret), 'utf-8'),
            msg=bytes(payload_str, 'utf-8'),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        response = requests.post(self.rest_endpoint+'private/create-order', json=req, headers={'Content-Type': 'application/json'})
        print(response.text)

if __name__ == '__main__':

    import os
    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv('CDCEX_API')
    secret_key = os.getenv('CDCEX_SECRET')

    cdc = CDC(api_key=api_key, secret_key=secret_key, sandbox=False)

    # # candles = cdc.get_candlesticks('BTC_USDC', '1m', 1000)

    # # print(len(candles))
    # # cdc.create_limit_order('BTC_USDC', 'BUY', 10000, 1)

    print(cdc.create_market_order('ETH_USD', 'BUY', '0.0002', '2500', '4000'))

    # instruments = cdc.get_instruments()
    # for instrument in instruments['result']['data']:
    #     print(instrument['symbol'], instrument['inst_type'])