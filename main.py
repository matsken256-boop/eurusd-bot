import time, os, logging, pandas as pd
from datetime import datetime, timezone
from dotenv import load_dotenv

# Direct MT5 library - no MetaApi needed!
import MetaTrader5 as mt5

load_dotenv()

# YOUR EXNESS MT5 CREDENTIALS - add in VPS .env, NOT on GitHub!
MT5_LOGIN = int(os.getenv("MT5_LOGIN", "0"))  # your 486106174
MT5_PASSWORD = os.getenv("MT5_PASSWORD", "")
MT5_SERVER = os.getenv("MT5_SERVER", "Exness-MT5Trial10")
SYMBOL = os.getenv("SYMBOL", "EURUSD")
MA_PERIOD = int(os.getenv("MA_PERIOD", "5"))
LOT_SIZE = float(os.getenv("LOT_SIZE", "0.01"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()])

prices = []

def connect_mt5():
    # Initialize MT5
    if not mt5.initialize(login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER):
        logging.error(f"MT5 initialize failed: {mt5.last_error()}")
        return False
    logging.info(f"✅ Connected to Exness MT5 {MT5_LOGIN} on {MT5_SERVER}")
    return True

def get_price():
    tick = mt5.symbol_info_tick(SYMBOL)
    if tick:
        return tick.bid
    return None

def place_order(signal):
    # Prepare order request
    price = mt5.symbol_info_tick(SYMBOL).ask if signal == "BUY" else mt5.symbol_info_tick(SYMBOL).bid
    order_type = mt5.ORDER_TYPE_BUY if signal == "BUY" else mt5.ORDER_TYPE_SELL
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": LOT_SIZE,
        "type": order_type,
        "price": price,
        "sl": 0.0,
        "tp": 0.0,
        "deviation": 20,
        "magic": 234000,
        "comment": "eurusd-bot",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logging.error(f"Order failed: {result.retcode} {result.comment}")
    else:
        logging.info(f"✅ {signal} order placed: {LOT_SIZE} lots at {price}")

def run():
    if not connect_mt5():
        return
    
    global prices
    logging.info(f"Starting DIRECT Exness bot - MA{MA_PERIOD}")
    
    while True:
        price = get_price()
        if not price:
            time.sleep(5)
            continue
            
        prices.append(price)
        if len(prices) > 100: prices = prices[-100:]
        
        if len(prices) < MA_PERIOD:
            logging.info(f"Collecting prices... {len(prices)}/{MA_PERIOD}")
            time.sleep(60)
            continue
            
        ma = sum(prices[-MA_PERIOD:]) / MA_PERIOD
        signal = "BUY" if price > ma else "SELL" if price < ma else "WAIT"
        
        ts = datetime.now(timezone.utc).isoformat()
        logging.info(f"[{ts}] Price:{price:.5f} MA{MA_PERIOD}:{ma:.5f} Signal:{signal}")
        
        # Auto-trade if signal
        if signal in ["BUY", "SELL"]:
            # Check if we already have position
            positions = mt5.positions_get(symbol=SYMBOL)
            if not positions:  # No open position
                place_order(signal)
            else:
                logging.info(f"Position already open, skipping {signal}")
        
        # Save to CSV
        df = pd.DataFrame([[ts, price, ma, signal]], columns=["timestamp","price","ma","signal"])
        df.to_csv("eurusd_prices.csv", mode='a', header=not os.path.exists("eurusd_prices.csv"), index=False)
        
        time.sleep(60)

if __name__ == "__main__":
    run()
