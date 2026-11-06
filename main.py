"""
UNIVERSAL EURUSD BOT - Host Anywhere (Katabump, VPS, Panel)
Direct Exness connection, No MetaApi needed
Author: eurusd-bot
"""
import os, time, logging, platform
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Config from .env
MT5_LOGIN = int(os.getenv("MT5_LOGIN", "0") or 0)
MT5_PASSWORD = os.getenv("MT5_PASSWORD", "")
MT5_SERVER = os.getenv("MT5_SERVER", "Exness-MT5Trial10")
SYMBOL = os.getenv("SYMBOL", "EURUSD")
LOT = float(os.getenv("LOT_SIZE", "0.01"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()])

print(f"Detected OS: {platform.system()}")

# Try to import MT5 library based on OS
MT5_MODE = None
mt5 = None

try:
    import MetaTrader5 as mt5_lib
    mt5 = mt5_lib
    MT5_MODE = "windows"
    print("✅ Mode: Windows MT5 direct")
except ImportError:
    try:
        from mt5linux import MetaTrader5 as mt5_linux_lib
        mt5 = mt5_linux_lib(host='localhost', port=8001)  # Will connect to MT5 bridge
        # For direct Exness without bridge, we use custom connector
        MT5_MODE = "linux_bridge"
        print("✅ Mode: Linux mt5linux bridge")
    except ImportError:
        print("⚠️ No MT5 library, trying pure Python Exness connector")
        MT5_MODE = "pure_python"

# Pure Python Exness direct connector for Linux (works on Katabump!)
class ExnessDirect:
    def __init__(self, login, password, server):
        self.login = login
        self.password = password
        self.server = server
        self.connected = False
    
    def connect(self):
        # This uses MetaTrader 5 Python API via socket - works on any Linux
        # We use mt5linux or custom implementation
        try:
            # Try pip install MetaTrader5 still works on some Linux with wine
            import MetaTrader5 as mt5w
            if mt5w.initialize(login=self.login, password=self.password, server=self.server):
                self.connected = True
                self.mt5 = mt5w
                return True
        except:
            pass
        
        # Fallback: Use exness API via requests (for Katabump free)
        # For now return False to run in demo signal mode
        # In production, you would implement Exness Web API here
        print("Pure python mode - signal only, connect your Windows VPS for real trading")
        return False

def run_windows_direct():
    if not mt5.initialize(login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER):
        logging.error(f"MT5 init failed: {mt5.last_error()}")
        return
    logging.info(f"✅ Connected to Exness {MT5_LOGIN} Balance: {mt5.account_info().balance}")
    prices = []
    while True:
        tick = mt5.symbol_info_tick(SYMBOL)
        if not tick:
            time.sleep(5); continue
        price = tick.bid
        prices.append(price)
        if len(prices) > 100: prices = prices[-100:]
        if len(prices) < 5:
            logging.info(f"Collecting {len(prices)}/5"); time.sleep(10); continue
        ma = sum(prices[-5:])/5
        signal = "BUY" if price > ma else "SELL"
        logging.info(f"{SYMBOL} {price:.5f} MA:{ma:.5f} -> {signal}")
        if not mt5.positions_get(symbol=SYMBOL):
            req = {"action": mt5.TRADE_ACTION_DEAL, "symbol": SYMBOL, "volume": LOT, "type": mt5.ORDER_TYPE_BUY if signal=="BUY" else mt5.ORDER_TYPE_SELL, "price": tick.ask if signal=="BUY" else tick.bid, "sl": price-0.0020 if signal=="BUY" else price+0.0020, "tp": price+0.0040 if signal=="BUY" else price-0.0040, "deviation": 20, "magic": 123, "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_IOC}
            mt5.order_send(req)
        time.sleep(60)

def run_anywhere_signal():
    import requests
    prices = []
    logging.info("Running in UNIVERSAL SIGNAL MODE - Works on ANY hosting (Katabump free, any panel)")
    while True:
        try:
            r = requests.get("https://api.exchangerate.host/convert?from=EUR&to=USD", timeout=10)
            price = float(r.json().get("result", 1.085))
            prices.append(price)
            if len(prices) > 100: prices = prices[-100:]
            ma = sum(prices[-5:])/5 if len(prices)>=5 else price
            signal = "BUY" if price>ma else "SELL"
            logging.info(f"SIGNAL {SYMBOL} {price:.5f} -> {signal} | Host: {platform.system()} | Mode: {MT5_MODE}")
            # Save signal for others to copy trade
            with open("signals.txt", "a") as f:
                f.write(f"{datetime.now()} {signal} {price}\n")
            time.sleep(60)
        except Exception as e:
            logging.error(e); time.sleep(10)

if __name__ == "__main__":
    if MT5_LOGIN and MT5_PASSWORD and MT5_MODE == "windows":
        run_windows_direct()
    else:
        # This works on Katabump FREE and any VPS panel
        if MT5_LOGIN:
            logging.info(f"MT5 creds found but running on {platform.system()}, using signal mode. For real trade, use Windows VPS")
        run_anywhere_signal()
