import os, time
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
from fxapis import Fxapis

print("MATSKEN RSI SMART BOT - Buy Low Sell High")

def is_market_open():
    now = datetime.utcnow()
    wd, hr = now.weekday(), now.hour
    if wd == 5: return False
    if wd == 6 and hr < 22: return False
    if wd == 4 and hr >= 22: return False
    return True

def calculate_rsi(prices, period=14):
    if len(prices) < period+1:
        return 50
    gains = 0
    losses = 0
    for i in range(1, period+1):
        change = prices[-i] - prices[-i-1]
        if change > 0:
            gains += change
        else:
            losses += abs(change)
    avg_gain = gains / period
    avg_loss = losses / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

client = Fxapis()
LOGIN=os.getenv("MT5_LOGIN")
PWD=os.getenv("MT5_PASSWORD")
SERVER=os.getenv("MT5_SERVER")
SYMBOL=os.getenv("SYMBOL", "EURUSD")
VOL=float(os.getenv("VOLUME", "0.01"))

RSI_BUY = 30
RSI_SELL = 70
STOP_LOSS = 50
TAKE_PROFIT = 80

print(f"Broker: {SERVER}")
print(f"Symbol: {SYMBOL}")
print(f"RSI Buy <{RSI_BUY} | Sell >{RSI_SELL}")

try:
    acc = client.accounts.connect(login=LOGIN, password=PWD, server=SERVER, mode="warm_on_demand", label="PublicBot")
    acc_id = acc["id"]
    print("Connected")
except:
    acc_id = client.accounts.list()[0]["id"]
    print(f"Using saved account {acc_id}")

client.accounts.warm(acc_id)
client.accounts.wait_until_ready(acc_id)
print("BOT READY")

price_history = []
in_trade = False
entry_price = 0

while True:
    try:
        if not is_market_open():
            print("Market Closed - sleep 1h")
            time.sleep(3600)
            continue

        current_price = 0
        try:
            candles = client.accounts.get_candles(acc_id, symbol=SYMBOL, timeframe="M5", count=20)
            if candles:
                current_price = float(candles[-1]['close'])
                for c in candles:
                    price_history.append(float(c['close']))
        except:
            pass

        if len(price_history) > 50:
            price_history = price_history[-50:]

        if len(price_history) < 15:
            print(f"Collecting prices for RSI... {len(price_history)}/15")
            time.sleep(10)
            if price_history:
                price_history.append(price_history[-1] + 0.0001)
            else:
                price_history.append(1.1020)
            continue

        rsi = calculate_rsi(price_history, 14)
        current_price = price_history[-1]

        print(f"{SYMBOL}: {current_price:.5f} | RSI: {rsi:.1f}")

        if not in_trade:
            if rsi < RSI_BUY:
                print(f"RSI LOW {rsi:.1f} - BUYING!")
                try:
                    order = client.orders.market(acc_id, symbol=SYMBOL, side="buy", volume=VOL)
                    entry_price = float(order.get('price', current_price))
                    in_trade = True
                    print(f"BOUGHT @ {entry_price}")
                except Exception as be:
                    print(f"Buy failed: {be}")
            else:
                print(f"RSI {rsi:.1f} not low enough -
