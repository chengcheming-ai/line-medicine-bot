"""
LINE 吃藥提醒推播
1. 依目前時段生成提醒圖片
2. 上傳至 GitHub repo 取得公開 HTTPS URL
3. 透過 LINE Push API 發送圖片訊息至個人帳號
"""
import os, base64, time, logging, requests
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler
from generate_reminder import generate

load_dotenv()

TOKEN    = os.getenv("CHANNEL_ACCESS_TOKEN")
USER_ID  = os.getenv("USER_ID")
IMG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reminder.jpg")

# ── logging ──────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
_handler = RotatingFileHandler("logs/bot.log", maxBytes=100_000, backupCount=3, encoding="utf-8")
_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S"))
log = logging.getLogger("reminder")
log.setLevel(logging.INFO)
log.addHandler(_handler)
log.addHandler(logging.StreamHandler())

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO         = "chengcheming-ai/line-medicine-bot"
IMG_RAW_URL  = f"https://raw.githubusercontent.com/{REPO}/master/images/reminder.jpg"

# ── 1. 生成圖片 ───────────────────────────────────────────────
log.info("開始生成提醒圖片")
generate(slot=None, out_path=IMG_PATH)
log.info("圖片生成完成: %s", IMG_PATH)

# ── 2. 上傳至 GitHub repo ─────────────────────────────────────
def upload_image(path):
    if not GITHUB_TOKEN:
        log.warning("無 GITHUB_TOKEN，跳過圖片上傳")
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
        log.error("GitHub 上傳失敗: %s", r.status_code)
        return None
    for i in range(5):
        time.sleep(3)
        check = requests.get(IMG_RAW_URL, timeout=10)
        if check.status_code == 200 and "image" in check.headers.get("Content-Type", ""):
            log.info("GitHub 上傳 OK: %s", IMG_RAW_URL)
            return IMG_RAW_URL
        log.info("等待 CDN (%d/5)...", i + 1)
    log.error("CDN 逾時，圖片無法取得")
    return None

img_url = upload_image(IMG_PATH)

# ── 3. 發送 LINE 訊息 ─────────────────────────────────────────
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TOKEN}",
}

if img_url:
    msg = [{"type": "image", "originalContentUrl": img_url, "previewImageUrl": img_url}]
else:
    msg = [{"type": "text", "text": "記得吃藥喔！耶穌愛你，主與你同在。"}]

for target_id, label in [(USER_ID, "個人"), (os.getenv("GROUP_ID"), "群組")]:
    if not target_id:
        continue
    resp = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers=headers,
        json={"to": target_id, "messages": msg},
        timeout=15,
    )
    if resp.status_code == 200:
        log.info("LINE 推播(%s) OK", label)
    else:
        log.error("LINE 推播(%s) FAIL (%s) %s", label, resp.status_code, resp.text)
