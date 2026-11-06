import time, os, logging, requests, pandas as pd
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()
SYMBOL = os.getenv("SYMBOL", "EURUSD")
MA_PERIOD = int(os.getenv("MA_PERIOD", "5"))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()])
prices = []
def get_price():
    try:
        r = requests.get("https://api.exchangerate.host/convert?from=EUR&to=USD", timeout=10)
        if r.json().get("result"): return float(r.json()["result"])
        r2 = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}=X?interval=1m&range=1d", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        closes = r2.json()["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        return float([c for c in closes if c is not None][-1])
    except Exception as e:
        logging.error(f"Error: {e}")
        return None
def run():
    global prices
    while True:
        price = get_price()
        if price is None:
            time.sleep(CHECK_INTERVAL); continue
        prices.append(price)
        if len(prices) > 100: prices = prices[-100:]
        ma = sum(prices[-MA_PERIOD:])/MA_PERIOD if len(prices) >= MA_PERIOD else 0
        signal = "BUY" if ma and price > ma else "SELL" if ma and price < ma else "WAIT"
        ts = datetime.now(timezone.utc).isoformat()
        logging.info(f"Price:{price:.5f} MA:{ma:.5f} Signal:{signal}")
        df = pd.DataFrame([[ts, price, ma, signal]], columns=["timestamp","price","ma","signal"])
        df.to_csv("eurusd_prices.csv", mode='a', header=not os.path.exists("eurusd_prices.csv"), index=False)
        time.sleep(CHECK_INTERVAL)
if __name__ == "__main__": run()
