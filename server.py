from flask import Flask, jsonify, session, request, redirect
from flask_cors import CORS
import threading
import time
import websocket
import json
from trader import Trader
import sqlite3


app = Flask(__name__)
CORS(app)
app.secret_key = "intrades_secret_key"

bot_running = False

users = {
    "default": {
        "wins": 0,
        "losses": 0,
        "price": 0,
        "bot_running": False
    }
}

current_user = "default"

trader = Trader("Tn569d6qVdp2fiA")

def init_db():
    conn = sqlite3.connect("intrades.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    conn.commit()
    conn.close()

def on_message(ws, message):
    global price
    data = json.loads(message)

    if "tick" in data:
        price = float(data["tick"]["quote"])


def on_open(ws):
    ws.send(json.dumps({
        "ticks": "R_75"
    }))


def start_deriv_feed():
    app_id = "1089"
    url = f"wss://ws.derivws.com/websockets/v3?app_id={app_id}"

    ws = websocket.WebSocketApp(
        url,
        on_message=on_message,
        on_open=on_open
    )

    ws.run_forever()

def place_trade(signal):
    print("Trade sent:", signal)
    return "win"


prices = []
last_trade_time = 0

def trading_bot():
    global bot_running, price, wins, losses, last_trade_time

    while bot_running:
        prices.append(price)

        if len(prices) > 50:
            prices.pop(0)

        if len(prices) < 20:
            time.sleep(1)
            continue

        if time.time() - last_trade_time < 10:
            time.sleep(1)
            continue

        ma_short = sum(prices[-5:]) / 5
        ma_long = sum(prices[-20:]) / 20

        signal = "CALL" if ma_short > ma_long else "PUT" if ma_short < ma_long else None

        if signal:
            trader.buy(signal)
            last_trade_time = time.time()
            wins = trader.wins
            losses = trader.losses

        time.sleep(1)

@app.route("/start")
def start():
    global current_user

    users[current_user]["bot_running"] = True

    threading.Thread(target=trading_bot).start()

    return jsonify({"status": "running"})


@app.route("/stop")
def stop():
    users[current_user]["bot_running"] = False
    return jsonify({"status": "stopped"})


@app.route("/status")
def status():
    user = users[current_user]

    return jsonify({
        "running": user["bot_running"],
        "price": user["price"],
        "wins": user["wins"],
        "losses": user["losses"]
    })
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute(
         "SELECT * FROM users WHERE username=? AND password=?",
         (username, password)
)

        user = c.fetchone()
        conn.close()

    if user:
        session["user"] = username
        return redirect("/")

    return """

    <form method="POST">
        <input name="username" placeholder="username"/>
        <input name="password" placeholder="password"/>
        <button type="submit">Login</button>
    </form>
    """
 
@app.route("/")
def dashboard():
    return """
    <html>
    <head>
        <title>Intrades Dashboard</title>
        <style>
            body { font-family: Arial; background:#111; color:#fff; text-align:center; }
            .card { margin:20px auto; padding:20px; width:300px; background:#222; border-radius:10px; }
            button { padding:10px 20px; margin:10px; cursor:pointer; }
        </style>
    </head>
    <body>
        <h1>Intrades Pro Dashboard</h1>

        <div class="card">
            <p>Bot Status: <span id="status">-</span></p>
            <p>Price: <span id="price">-</span></p>
            <p>Wins: <span id="wins">-</span></p>
            <p>Losses: <span id="losses">-</span></p>

            <button onclick="fetch('/start')">Start</button>
            <button onclick="fetch('/stop')">Stop</button>
        </div>

        <script>
        async function update(){
            let res = await fetch('/status');
            let data = await res.json();

            document.getElementById('status').innerText = data.running;
            document.getElementById('price').innerText = data.price;
            document.getElementById('wins').innerText = data.wins;
            document.getElementById('losses').innerText = data.losses;
        }

        setInterval(update, 1000);
        update();
        </script>
    </body>
    </html>
    """
init_db()


import os

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))