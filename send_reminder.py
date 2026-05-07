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

# ── 2. 上傳圖片取得 HTTPS URL（catbox → 0x0.st 備援）────────
def upload_image(path):
    with open(path, "rb") as f:
        data = f.read()

    uploaders = [
        ("catbox",      lambda: _upload_catbox(data)),
        ("litterbox",   lambda: _upload_litterbox(data)),
        ("transfer.sh", lambda: _upload_transfer(data)),
        ("0x0.st",      lambda: _upload_0x0(data)),
    ]
    for name, fn in uploaders:
        try:
            url = fn()
            if url and url.startswith("https://"):
                print(f"[upload] {name} OK: {url}")
                return url
            print(f"[upload] {name} 無效回應")
        except Exception as e:
            print(f"[upload] {name} 失敗: {e}")
    return None

def _upload_catbox(data):
    r = requests.post(
        "https://catbox.moe/user/api.php",
        data={"reqtype": "fileupload"},
        files={"fileToUpload": ("reminder.jpg", data, "image/jpeg")},
        timeout=20,
    )
    return r.text.strip()

def _upload_litterbox(data):
    r = requests.post(
        "https://litterbox.catbox.moe/resources/internals/api.php",
        data={"reqtype": "fileupload", "time": "72h"},
        files={"fileToUpload": ("reminder.jpg", data, "image/jpeg")},
        timeout=20,
    )
    return r.text.strip()

def _upload_transfer(data):
    r = requests.put(
        "https://transfer.sh/reminder.jpg",
        data=data,
        headers={"Content-Type": "image/jpeg", "Max-Downloads": "10", "Max-Days": "1"},
        timeout=20,
    )
    return r.text.strip()

def _upload_0x0(data):
    r = requests.post(
        "https://0x0.st",
        files={"file": ("reminder.jpg", data, "image/jpeg")},
        timeout=20,
    )
    return r.text.strip()

img_url = upload_image(IMG_PATH)

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
