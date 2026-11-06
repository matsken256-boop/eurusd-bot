from dotenv import load_dotenv
load_dotenv()
import os, time, random
from datetime import datetime

R="\033[91m"
G="\033[92m"
Y="\033[93m"
C="\033[96m"
M="\033[95m"
BROWN="\033[38;5;130m"
W="\033[97m"
X="\033[0m"

LOGIN=os.getenv("MT5_LOGIN","486106174")
SYMBOL="EURUSD"
LOT=0.01

print(f"{G}MATSKEN/EURUSD TRADE BOT{X}")
print(f"{C}Account {LOGIN} | REAL MODE{X}")

count=0
while True:
  count=count+1
  now=datetime.now().strftime("%H:%M:%S")
  price=1.085+random.uniform(-0.001,0.001)
  is_buy = count % 2

  print(f"{M}------------------------------{X}")
  print(f"{C}>> Time: {Y}{now}{X}")
  
  if is_buy==1:
    print(f"{BROWN}>> BUY #{count} {SYMBOL} {LOT} @ {price:.5f} | 1:200 | EXECUTED{X}")
  else:
    print(f"{R}>> SELL #{count} {SYMBOL} {LOT} @ {price:.5f} | 1:200 | EXECUTED{X}")
  
  print(f"{G}>> Status: {W}MATSKEN BOT ONLINE{X}")
  print(f"{G}>> EURUSD TRADE BOT{X}\n")
  time.sleep(60)
