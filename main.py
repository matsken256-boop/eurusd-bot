import os, time
from dotenv import load_dotenv
load_dotenv()
from fxapis import Fxapis

G="\033[92m"; R="\033[91m"; Y="\033[93m"; C="\033[96m"; M="\033[95m"; W="\033[97m"; B="\033[94m"; X="\033[0m"

print(f"{C}╔════════════════════════════════╗{X}")
print(f"{C}║ {M}MATSKEN FOREX - ANY BROKER   {C}║{X}")
print(f"{C}╚════════════════════════════════╝{X}")

client = Fxapis()

# Read ANY broker from .env - not just Exness!
LOGIN=os.getenv("MT5_LOGIN")
PWD=os.getenv("MT5_PASSWORD")
SERVER=os.getenv("MT5_SERVER")
SYMBOL=os.getenv("SYMBOL", "EURUSD")
VOL=os.getenv("VOLUME", "0.01")

print(f"{B}>> 🟢 Broker: {W}{SERVER}{X}")
print(f"{B}>> 🟢 Login: {W}{LOGIN}{X}")
print(f"{B}>> 🟢 Symbol: {W}{SYMBOL}{X}")

# Connect to ANY MT5 account (Exness, IC, Deriv, FBS, XM...)
try:
    acc = client.accounts.connect(login=LOGIN, password=PWD, server=SERVER, mode="warm_on_demand", label="PublicBot")
    acc_id = acc["id"]
    print(f"{G}>> ✅ Connected to {SERVER}{X}")
except:
    # Already connected
    acc_id = client.accounts.list()[0]["id"]
    print(f"{G}>> ✅ Using saved account {acc_id}{X}")

client.accounts.warm(acc_id)
client.accounts.wait_until_ready(acc_id)
print(f"{G}>> ✅ REAL TRADING READY - Any Broker!{X}")

while True:
    try:
        print(f"{C}>> 🔵 Asking {SERVER} for {W}{SYMBOL} price...{X}")
        order = client.orders.market(acc_id, symbol=SYMBOL, side="buy", volume=VOL)
        price = order.get('price','')
        print(f"{G}╔══════════════════════════════════╗{X}")
        print(f"{G}║ ✅ MARKET OPEN! {SYMBOL} @ {price}  ║{X}")
        print(f"{G}╚══════════════════════════════════╝{X}")
        time.sleep(60)
        client.orders.market(acc_id, symbol=SYMBOL, side="sell", volume=VOL)
        print(f"{R}>> ✅ SELL CLOSED{X}")
        time.sleep(60)
    except Exception as e:
        real_msg = str(e)
        print(f"{Y}>> ⚠️ Broker says: {W}{real_msg[:300]}{X}")
        if "NO_PRICE" in real_msg or "422" in real_msg:
            print(f"{Y}>> ⏳ Market CLOSED - waiting 5 min...{X}")
            time.sleep(300)
        else:
            time.sleep(30)
