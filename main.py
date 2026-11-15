import os, time
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
from fxapis import Fxapis

G="\033[92m"; R="\033[91m"; Y="\033[93m"; C="\033[96m"; M="\033[95m"; W="\033[97m"; B="\033[94m"; X="\033[0m"

print(f"{C}╔════════════════════════════════════╗{X}")
print(f"{C}║ {M}MATSKEN RSI SMART BOT - V3      {C}║{X}")
print(f"{C}║ {G}Buy <30 Sell >70 + SL/TP        {C}║{X}")
print(f"{C}╚════════════════════════════════════╝{X}")

def is_market_open():
    now = datetime.utcnow()
    wd, hr = now.weekday(), now.hour
    if wd == 5: return False
    if wd == 6 and hr < 22: return False
    if wd == 4 and hr >= 22: return False
    return True

def calculate_rsi(prices, period=14):
    """Calculate RSI - 0 to 100"""
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

RSI_BUY = 30   # Buy when RSI < 30 (oversold = LOW)
RSI_SELL = 70  # Sell when RSI > 70 (overbought = HIGH)
STOP_LOSS = 50
TAKE_PROFIT = 80

print(f"{B}>> 🟢 Broker: {W}{SERVER} {X}")
print(f"{B}>> 🟢 Symbol: {W}{SYMBOL} {X}")
print(f"{B}>> 🟢 RSI: Buy <{RSI_BUY} | Sell >{RSI_SELL}{X}")
print(f"{B}>> 🟢 SL: {STOP_LOSS} pips | TP: {TAKE_PROFIT} pips{X}")

try:
    acc = client.accounts.connect(login=LOGIN, password=PWD, server=SERVER, mode="warm_on_demand", label="PublicBot")
    acc_id = acc["id"]
    print(f"{G}>> ✅ Connected{X}")
except:
    acc_id = client.accounts.list()[0]["id"]
    print(f"{G}>> ✅ Saved account {acc_id}{X}")

client.accounts.warm(acc_id)
client.accounts.wait_until_ready(acc_id)
print(f"{G}>> ✅ RSI BOT READY!{X}")

price_history = []
in_trade = False
entry_price = 0

while True:
    try:
        if not is_market_open():
            print(f"{Y}>> ⏳ Weekend closed - sleep 1h{X}")
            time.sleep(3600)
            continue

        # Get current price
        try:
            # Get price via positions/orders
            order_test = client.accounts.get_positions(acc_id) if hasattr(client.accounts, 'get_positions') else []
        except:
            pass

        # For price tracking - we get from latest order simulation
        # Try to get real market price from fxapis candles if available
        current_price = 0
        try:
            # Attempt to get candles - adjust if your fxapis version different
            candles = client.accounts.get_candles(acc_id, symbol=SYMBOL, timeframe="M5", count=20)
            if candles:
                current_price = float(candles[-1]['close'])
                for c in candles:
                    price_history.append(float(c['close']))
        except:
            # Fallback - use dummy tracking, will still work with RSI from history
            pass

        # Keep only last 50 prices
        if len(price_history) > 50:
            price_history = price_history[-50:]

        # If no price history yet, just wait
        if len(price_history) < 15:
            print(f"{C}>> 🔵 Collecting prices for RSI... {len(price_history)}/15{X}")
            # Make a test price fetch by doing small check
            try:
                # This will give us price without trading - using market check
                print(f"{C}>> 🔵 Waiting for {SYMBOL} price...{X}")
                time.sleep(10)
                # Add mock price for testing - replace with real price fetch
                # In real run, price_history will fill from candles
                price_history.append(price_history[-1] + 0.0001 if price_history else 1.1020)
            except:
                time.sleep(10)
            continue

        rsi = calculate_rsi(price_history, 14)
        current_price = price_history[-1]

        print(f"{C}>> 📊 {SYMBOL}: {W}{current_price:.5f} {C}| RSI: {W}{rsi:.1f}{X}")

        if not in_trade:
            if rsi < RSI_BUY:
                print(f"{G}╔══════════════════════════════════╗{X}")
                print(f"{G}║ 🟢 RSI LOW {rsi:.1f} < {RSI_BUY} - BUYING! ║{X}")
                print(f"{G}╚══════════════════════════════════╝{X}")
                try:
                    order = client.orders.market(acc_id, symbol=SYMBOL, side="buy", volume=VOL)
                    entry_price = float(order.get('price', current_price))
                    in_trade = True
                    print(f"{G}>> ✅ BOUGHT @ {entry_price} with SL {STOP_LOSS} TP {TAKE_PROFIT}{X}")
                except Exception as be:
                    print(f"{R}>> ❌ Buy failed: {be}{X}")
            else:
                print(f"{Y}>> ⏳ RSI {rsi:.1f} not low enough (<{RSI_BUY}) - Waiting...{X}")
        else:
            # In trade - check if should sell
            profit_pips = (current_price - entry_price) * 10000
            print(f"{Y}>> 🟡 In BUY @ {entry_price} | Now {current_price} | P/L: {profit_pips:.1f} pips | RSI: {rsi:.1f}{X}")
            
            if rsi > RSI_SELL or profit_pips >= TAKE_PROFIT or profit_pips <= -STOP_LOSS:
                reason = "RSI HIGH" if rsi > RSI_SELL else "TP HIT" if profit_pips >= TAKE_PROFIT else "SL HIT"
                print(f"{G}╔══════════════════════════════════╗{X}")
                print(f"{G}║ 🔴 SELLING - {reason} @ {current_price} ║{X}")
                print(f"{G}╚══════════════════════════════════╝{X}")
                try:
                    order = client.orders.market(acc_id, symbol=SYMBOL, side="sell", volume=VOL)
                    print(f"{G}>> ✅ CLOSED! P/L: {profit_pips:.1f} pips{X}")
                    in_trade = False
                    entry_price = 0
                except Exception as se:
                    print(f"{R}>> ❌ Sell failed: {se}{X}")

        time.sleep(60)

    except Exception as e:
        msg = str(e)
        print(f"{Y}>> ⚠️ {msg[:500]}{X}")
        if "NO_PRICE" in msg or "422" in msg:
            print(f"{Y}>> ⏳ Market closed - wait 5m{X}")
            time.sleep(300)
        else:
            time.sleep(30)
