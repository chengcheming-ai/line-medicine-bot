"""
LINE 吃藥提醒推播
1. 依目前時段生成提醒圖片
2. 上傳至 telegra.ph 取得公開 HTTPS URL
3. 透過 LINE Push API 發送圖片訊息
"""
import os, requests
from dotenv import load_dotenv
from generate_reminder import generate

load_dotenv()

TOKEN    = os.getenv("CHANNEL_ACCESS_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")
IMG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reminder.jpg")

# ── 1. 生成圖片（自動依時段選話語/經文/背景）────────────────
generate(slot=None, out_path=IMG_PATH)

# ── 2. 上傳至 catbox.moe 取得 HTTPS URL ─────────────────────
img_url = None
try:
    with open(IMG_PATH, "rb") as f:
        r = requests.post(
            "https://catbox.moe/user/api.php",
            data={"reqtype": "fileupload"},
            files={"fileToUpload": ("reminder.jpg", f, "image/jpeg")},
            timeout=30,
        )
    url = r.text.strip()
    if url.startswith("https://"):
        img_url = url
        print(f"上傳成功: {img_url}")
    else:
        raise ValueError(f"非預期回應: {url}")
except Exception as e:
    print(f"圖片上傳失敗，改傳文字: {e}")

# ── 3. 發送 LINE 訊息 ─────────────────────────────────────────
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TOKEN}",
}

if img_url:
    payload = {
        "to": GROUP_ID,
        "messages": [{
            "type": "image",
            "originalContentUrl": img_url,
            "previewImageUrl":    img_url,
        }],
    }
else:
    # 備用：純文字
    payload = {
        "to": GROUP_ID,
        "messages": [{"type": "text", "text": "記得吃藥喔！耶穌愛你，主與你同在。"}],
    }

resp = requests.post(
    "https://api.line.me/v2/bot/message/push",
    headers=headers,
    json=payload,
    timeout=15,
)
status = "OK" if resp.status_code == 200 else f"FAIL ({resp.status_code}: {resp.text})"
print(f"LINE 推播: {status}")
