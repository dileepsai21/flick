import ccxt
import asyncio
import websockets
import json
from config.config import API_KEY, API_SECRET

# Initialize Binance with ccxt (non-pro, REST API)
exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
})

# Example to fetch market data
markets = exchange.load_markets()
# print(markets)



async def binance_ws():
    uri = "wss://stream.binance.com:9443/ws/btcusdt@trade"
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            print(json.loads(message))

# Run WebSocket connection
asyncio.run(binance_ws())
