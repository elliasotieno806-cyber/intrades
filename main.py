from fastapi import FastAPI
import threading
from trader import Trader

app = FastAPI()

bot = None
running = False

TOKEN = "Tn569d6qVdp2fiA"

@app.get("/")
def home():
    return {"status": "Intrades running"}

def start_bot():
    global bot, running
    bot = Trader(TOKEN)
    bot.run()

@app.get("/start")
def start():
    global running
    if not running:
        running = True
        thread = threading.Thread(target=start_bot, daemon=True)
        thread.start()
    return {"status": "bot started"}