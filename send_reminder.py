"""
LINE 吃藥提醒推播
1. 依目前時段生成提醒圖片
2. 上傳至 telegra.ph 取得公開 HTTPS URL
3. 透過 LINE Push API 發送圖片訊息
"""
import os, base64, requests
from dotenv import load_dotenv
from generate_reminder import generate

load_dotenv()

TOKEN    = os.getenv("CHANNEL_ACCESS_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")
IMG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reminder.jpg")

# ── 1. 生成圖片（自動依時段選話語/經文/背景）────────────────
generate(slot=None, out_path=IMG_PATH)

# ── 2. 上傳圖片取得 HTTPS URL（catbox → 0x0.st 備援）────────
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO         = "chengcheming-ai/line-medicine-bot"
IMG_RAW_URL  = f"https://raw.githubusercontent.com/{REPO}/master/images/reminder.jpg"

def upload_image(path):
    if not GITHUB_TOKEN:
        print("[upload] 無 GITHUB_TOKEN，改傳文字")
        return None
    with open(path, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode()
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    api_url = f"https://api.github.com/repos/{REPO}/contents/images/reminder.jpg"
    sha = ""
    r = requests.get(api_url, headers=headers, timeout=10)
    if r.status_code == 200:
        sha = r.json().get("sha", "")
    body = {"message": "update reminder image", "content": content_b64}
    if sha:
        body["sha"] = sha
    r = requests.put(api_url, headers=headers, json=body, timeout=20)
    if r.status_code not in (200, 201):
        print(f"[upload] GitHub 失敗: {r.status_code} {r.text[:100]}")
        return None

    # 等待 CDN 傳播，最多確認 5 次
    import time
    for i in range(5):
        time.sleep(3)
        check = requests.get(IMG_RAW_URL, timeout=10)
        ct = check.headers.get("Content-Type", "")
        print(f"[check] status={check.status_code} Content-Type={ct}")
        if check.status_code == 200 and "image" in ct:
            print(f"[upload] GitHub OK: {IMG_RAW_URL}")
            return IMG_RAW_URL
        print(f"[upload] 等待 CDN ({i+1}/5)...")
    print("[upload] GitHub CDN 逾時")
    return None

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
