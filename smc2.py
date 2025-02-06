import asyncio
import websockets
import json
import pandas as pd
from datetime import datetime

class SmartMoneyBot:
    def __init__(self, api_token):
        self.api_token = api_token
        self.websocket_url = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
        self.websocket = None

    async def connect(self):
        self.websocket = await websockets.connect(self.websocket_url)
        await self.authenticate()

    async def authenticate(self):
        auth_request = {
            "authorize": self.api_token
        }
        await self.websocket.send(json.dumps(auth_request))
        response = await self.websocket.recv()
        data = json.loads(response)
        if "error" in data:
            print(f"Authentication failed: {data['error']['message']}")
        else:
            print("Successfully authenticated!")

    async def get_market_data(self, symbol, count=50):
        request = {
            "ticks_history": symbol,
            "count": count,
            "end": "latest",
            "style": "candles",
            "granularity": 60  # 1-minute candles
        }
        await self.websocket.send(json.dumps(request))
        response = await self.websocket.recv()
        data = json.loads(response)

        if "candles" in data:
            df = pd.DataFrame(data["candles"])
            df["epoch"] = pd.to_datetime(df["epoch"], unit="s")
            df.set_index("epoch", inplace=True)
            return df
        else:
            print("Error fetching market data:", data)
            return None

    async def place_order(self, symbol, amount, contract_type, duration=1):
        request = {
            "buy": 1,
            "subscribe": 1,
            "parameters": {
                "amount": amount,
                "basis": "stake",
                "contract_type": contract_type,
                "currency": "USD",
                "duration": duration,
                "duration_unit": "m",
                "symbol": symbol
            }
        }
        await self.websocket.send(json.dumps(request))
        response = await self.websocket.recv()
        print(f"Trade Response: {response}")

    async def analyze_market(self, symbol):
        data = await self.get_market_data(symbol)
        if data is not None:
            latest_price = data.iloc[-1]["close"]
            print(f"Latest price: {latest_price}")
            return "CALL" if latest_price % 2 == 0 else "PUT"  # Dummy strategy
        return None

    async def run(self, symbol, amount):
        await self.connect()
        while True:
            decision = await self.analyze_market(symbol)
            if decision:
                await self.place_order(symbol, amount, decision)
            else:
                print(f"{datetime.now()}: No trade signal")
            await asyncio.sleep(60)

if __name__ == "__main__":
    api_token = "WlKAzYujXhahCCe"  # Replace with your actual token
    bot = SmartMoneyBot(api_token)
    asyncio.run(bot.run("USDJPY", 10))  # Replace "R_100" with your chosen asset
