"""手動測試：傳送目前時間與任務狀態到個人 LINE 帳號"""
import os, requests
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

TOKEN   = os.getenv("CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

now = datetime.now(ZoneInfo("Asia/Taipei"))
time_str = now.strftime("%Y-%m-%d %H:%M")

message = (
    f"\U0001f916 機器人狀態通知\n"
    f"\U0001f552 目前時間：{time_str}（台北）\n"
    f"\n"
    f"\U0001f4cb 今日排程任務\n"
    f"  13:00 午餐後吃藥提醒\n"
    f"  20:00 晚餐後吃藥提醒\n"
    f"\n"
    f"✅ GitHub Actions 運作正常"
)

resp = requests.post(
    "https://api.line.me/v2/bot/message/push",
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TOKEN}",
    },
    json={"to": USER_ID, "messages": [{"type": "text", "text": message}]},
    timeout=10,
)

if resp.status_code == 200:
    print(f"OK: 通知已發送（{time_str}）")
else:
    print(f"FAIL ({resp.status_code}): {resp.text}")
    exit(1)
