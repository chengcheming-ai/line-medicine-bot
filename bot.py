import os
import time
import logging
import requests
import schedule
from datetime import datetime
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

load_dotenv()

TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")

# ── logging ──────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
_handler = RotatingFileHandler("logs/bot.log", maxBytes=100_000, backupCount=3, encoding="utf-8")
_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S"))
log = logging.getLogger("bot")
log.setLevel(logging.INFO)
log.addHandler(_handler)
log.addHandler(logging.StreamHandler())

def send_message(text: str):
    resp = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TOKEN}",
        },
        json={
            "to": GROUP_ID,
            "messages": [{"type": "text", "text": text}],
        },
        timeout=10,
    )
    if resp.status_code == 200:
        log.info("推播 OK")
    else:
        log.error("推播 FAIL (%s) %s", resp.status_code, resp.text)

def remind():
    log.info("觸發提醒")
    send_message("記得吃藥喔 ❤️")

schedule.every().day.at("13:00").do(remind)
schedule.every().day.at("20:00").do(remind)
schedule.every().day.at("23:30").do(remind)

log.info("機器人啟動，每天 13:00 / 20:00 / 23:30 推播")

while True:
    schedule.run_pending()
    time.sleep(30)
