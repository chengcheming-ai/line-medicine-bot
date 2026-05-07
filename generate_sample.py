from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import requests, io, math

W, H = 720, 820
MSJH = "C:/Windows/Fonts/msjh.ttc"

def f(size):
    return ImageFont.truetype(MSJH, size)

def centered(draw, text, y, font, color):
    bb = draw.textbbox((0, 0), text, font=font)
    w = bb[2] - bb[0]
    draw.text(((W - w) // 2, y), text, fill=color, font=font)

def divider(draw, y, pad=65, color=(180, 148, 60)):
    draw.line([(pad, y), (W - pad, y)], fill=color, width=1)

# ── 1. 下載真實風景照片作為背景 ─────────────────────────────
CANDIDATES = [
    # 金色日落海面
    "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=720&h=820&fit=crop&q=80",
    # 溫暖夕陽草原
    "https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?w=720&h=820&fit=crop&q=80",
    # 陽光向日葵花海
    "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=720&h=820&fit=crop&q=80",
    # 湖面倒影晨光
    "https://images.unsplash.com/photo-1501854140801-50d01698950b?w=720&h=820&fit=crop&q=80",
    # 備用 picsum（隨機風景）
    "https://picsum.photos/seed/sunset/720/820",
]

bg = None
for url in CANDIDATES:
    try:
        print(f"嘗試下載: {url[:60]}...")
        resp = requests.get(url, timeout=15, allow_redirects=True)
        if resp.status_code == 200 and "image" in resp.headers.get("Content-Type", ""):
            bg = Image.open(io.BytesIO(resp.content)).convert("RGB").resize((W, H), Image.LANCZOS)
            print("下載成功")
            break
    except Exception as e:
        print(f"失敗: {e}")

if bg is None:
    print("所有圖源失敗，使用漸層備用背景")
    bg = Image.new("RGB", (W, H))
    bd = ImageDraw.Draw(bg)
    for y in range(H):
        t = y / H
        r = int(255 - t * 60)
        g = int(180 - t * 80)
        b = int(80  + t * 20)
        bd.line([(0, y), (W, y)], fill=(r, g, b))

# ── 2. 背景稍微提亮 + 輕微模糊（讓文字更清晰）─────────────
bg = ImageEnhance.Brightness(bg).enhance(1.08)
bg = bg.filter(ImageFilter.GaussianBlur(radius=1.5))

# ── 3. 半透明文字面板 ─────────────────────────────────────────
PANEL_T1, PANEL_T2 = 25, 398   # 上方面板
PANEL_B1, PANEL_B2 = 415, 678  # 下方面板

overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
od = ImageDraw.Draw(overlay)
od.rounded_rectangle([25, PANEL_T1, W - 25, PANEL_T2], radius=20, fill=(255, 252, 240, 200))
od.rounded_rectangle([25, PANEL_B1, W - 25, PANEL_B2], radius=20, fill=(255, 252, 240, 192))
img = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
draw = ImageDraw.Draw(img)

# ── 4. 顏色 ─────────────────────────────────────────────────
GOLD  = (158, 110, 10)
RED   = (148, 28, 28)
NAVY  = (28,  48, 115)
BROWN = (120, 78, 15)
DARK  = (50,  42, 30)

# ── 5. 上方面板：十字架 + 提醒 ──────────────────────────────
cx, cy = W // 2, 55
draw.rectangle([cx - 6, cy,      cx + 6, cy + 85], fill=GOLD)
draw.rectangle([cx - 42, cy + 26, cx + 42, cy + 41], fill=GOLD)

for ang in range(0, 360, 40):
    rad = math.radians(ang)
    ox, oy = cx, cy + 43
    x1 = ox + 56 * math.cos(rad)
    y1 = oy + 56 * math.sin(rad)
    x2 = ox + 74 * math.cos(rad)
    y2 = oy + 74 * math.sin(rad)
    draw.line([(x1, y1), (x2, y2)], fill=GOLD, width=2)

for ax, ay in [(40, 34), (W - 56, 34), (40, 363), (W - 56, 363)]:
    draw.rectangle([ax, ay, ax + 12, ay + 12], outline=GOLD, width=2)

centered(draw, "記得吃藥喔！",              158, f(62), RED)
centered(draw, "耶穌愛你，時刻牽掛您的健康", 240, f(30), BROWN)

divider(draw, 298)
centered(draw, "健康是神賜給我們的恩典", 314, f(27), DARK)
centered(draw, "好好保重，主與你同在",   352, f(27), DARK)

# ── 6. 下方面板：經文 ───────────────────────────────────────
divider(draw, 432, pad=55)
centered(draw, "你們要將一切的憂慮卸給神，", 452, f(30), NAVY)
centered(draw, "因為祂顧念你們。",           496, f(30), NAVY)
centered(draw, "彼得前書 5 : 7",             542, f(26), NAVY)
divider(draw, 585, pad=55)
centered(draw, "願平安與你同在",             604, f(36), GOLD)

# ── 7. 外框 ─────────────────────────────────────────────────
draw.rectangle([ 7,  7, W -  7, H -  7], outline=GOLD, width=4)
draw.rectangle([14, 14, W - 14, H - 14], outline=(210, 170, 45), width=1)

out = "D:/Claude/line-medicine-bot/sample_reminder.jpg"
img.save(out, quality=93)
print(f"Done: {out}")
