import websocket, json, time, random

class Trader:
    def __init__(self, token):
        self.token = token
        self.ws = websocket.WebSocket()
        self.ws.connect("wss://ws.derivws.com/websockets/v3?app_id=1089")

        self.ws.send(json.dumps({"authorize": self.token}))
        
        auth_response = json.loads(self.ws.recv())
        print("AUTH:", auth_response)

        print("CONNECTED")

        self.prices = []
        self.last_trade_time =0 
        self.wins = 0
        self.losses = 0
        self.running = False

    def get_live_price(self):
        return 5

    def buy(self, contract_type):
        print("SENDING TRADE:", contract_type)

        self.ws.send(json.dumps({
            "buy": 1,
            "price": 1,
            "parameters": {
                "amount": 1,
                "basis": "stake",
                "contract_type": contract_type,
                "currency": "USD",
                "duration": 5,
                "duration_unit": "t",
                "symbol": "R_100"
           }
        }))

        response = json.loads(self.ws.recv())

        if "buy" not in response:
            print("BUY FAILED:", response)
            return

        if "buy" in response:
            contract_id = response["buy"]["contract_id"]
            print("TRADE ID:", contract_id)

        self.ws.send(json.dumps({
            "proposal_open_contract": 1,
            "contract_id": contract_id,
            "subscribe": 1
        }))

    def run(self):
        print("BOT RUN STARTED")

        self.ws.send(json.dumps({
            "ticks": "R_100",
            "subscribe": 1
        }))

        self.running = True

        while self.running:
            data = json.loads(self.ws.recv())

            if "tick" in data:
                price = float(data["tick"]["quote"])
                print("PRICE:", price)

                self.prices.append(price)

            if len(self.prices) < 5:
                continue

            avg = sum(self.prices[-5:]) / 5

            now = time.time()

            if now - self.last_trade_time < 5:
                continue

            if price > avg:
                self.buy("CALL")
            else:
                self.buy("PUT")

            self.last_trade_time = now

def stop(self):
    self.running = False
    print("Bot stopped")

if __name__ == "__main__":
    token = "Tn569d6qVdp2fiA"
    bot = Trader(token)
    bot.run()       