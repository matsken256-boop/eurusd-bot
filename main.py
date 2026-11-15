import os, time
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

import MetaTrader5 as mt5

print("MATSKEN FREE MT5 BOT - NO FXAPIS NEEDED")

def is_market_open():
    now = datetime.utcnow()
    wd = now.weekday()
    hr = now.hour
    if wd == 5:
        return False
    if wd == 6 and hr < 22:
        return False
    if wd == 4 and hr >= 22:
        return False
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

LOGIN = int(os.getenv("MT5_LOGIN"))
PASSWORD = os.getenv("MT5_PASSWORD")
SERVER = os.getenv("MT5_SERVER")
SYMBOL = os.getenv("SYMBOL", "EURUSD")
VOL = float(os.getenv("VOLUME", "0.01"))

print("Broker:", SERVER)
print("Symbol:", SYMBOL)
print("Login:", LOGIN)

# Initialize MT5
if not mt5.initialize(login=LOGIN, password=PASSWORD, server=SERVER):
    print("MT5 initialize failed:", mt5.last_error())
    mt5.shutdown()
    exit()

print("Connected to MT5 - BOT READY")

# Make sure symbol is visible
mt5.symbol_select(SYMBOL, True)

price_history = []
in_trade = False
entry_price = 0
RSI_BUY = 30
RSI_SELL = 70

while True:
    try:
        if not is_market_open():
            print("Market Closed - sleep 1h")
            time.sleep(3600)
            continue

        # Get last 30 candles M5
        rates = mt5.copy_rates_from_pos(SYMBOL, mt5.TIMEFRAME_M5, 0, 30)
        if rates is None or len(rates) == 0:
            print("No price data - retry")
            time.sleep(10)
            continue

        price_history = [float(x['close']) for x in rates]
        current_price = price_history[-1]
        rsi = calculate_rsi(price_history, 14)

        print(SYMBOL, round(current_price, 5), "RSI", round(rsi, 1))

        # Count open positions
        positions = mt5.positions_get(symbol=SYMBOL)
        has_position = positions is not None and len(positions) > 0

        if not has_position:
            if rsi < RSI_BUY:
                print("RSI LOW - BUYING!")
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": SYMBOL,
                    "volume": VOL,
                    "type": mt5.ORDER_TYPE_BUY,
                    "price": mt5.symbol_info_tick(SYMBOL).ask,
                    "deviation": 20,
                    "magic": 234000,
                    "comment": "RSI Bot Buy",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
                result = mt5.order_send(request)
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    print("BOUGHT at", result.price)
                else:
                    print("Buy failed:", result.retcode, result.comment)
            else:
                print("RSI not low enough - Waiting")
        else:
            # We have a position - check profit
            pos = positions[0]
            profit = pos.profit
            pos_price = pos.price_open
            # Get current price
            tick = mt5.symbol_info_tick(SYMBOL)
            current = tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask
            profit_pips = (current - pos_price) * 10000 if pos.type == 0 else (pos_price - current) * 10000
            
            print("In trade P/L", round(profit, 2), "$", round(profit_pips, 1), "pips RSI", round(rsi,1))

            if rsi > RSI_SELL or profit_pips >= 80 or profit_pips <= -50:
                print("CLOSING TRADE - RSI HIGH or TP/SL")
                # Close position
                close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
                close_request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": SYMBOL,
                    "volume": pos.volume,
                    "type": close_type,
                    "position": pos.ticket,
                    "price": tick.bid if pos.type == 0 else tick.ask,
                    "deviation": 20,
                    "magic": 234000,
                    "comment": "RSI Bot Close",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
                result = mt5.order_send(close_request)
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    print("CLOSED PROFIT", profit)
                else:
                    print("Close failed:", result.comment)

        time.sleep(60)

    except Exception as e:
        print("Error:", str(e)[:300])
        time.sleep(30)
