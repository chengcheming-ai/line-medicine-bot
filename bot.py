import os
import time
import requests
import schedule
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")

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
    status = "OK" if resp.status_code == 200 else f"FAIL ({resp.status_code})"
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 推播 {status}")

def remind():
    send_message("記得吃藥喔 ❤️")

schedule.every().day.at("13:00").do(remind)
schedule.every().day.at("20:00").do(remind)
schedule.every().day.at("23:30").do(remind)

print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] 提醒機器人啟動，每天 13:00 / 20:00 / 23:30 推播")

while True:
    schedule.run_pending()
    time.sleep(30)
