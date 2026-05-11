"""
LINE 吃藥提醒圖片生成器
- 依時段隨機選取關心話語
- 隨機選取聖經經文
- 隨機選取風景背景
用法: python generate_reminder.py [afternoon|evening|night] [output_path]
"""
import sys, os, random, requests, io, math
from datetime import datetime
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

W, H = 720, 718

if sys.platform == "win32":
    MSJH = "C:/Windows/Fonts/msjh.ttc"
else:
    MSJH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

# ── 時段關心話語 ─────────────────────────────────────────────
MESSAGES = {
    "afternoon": [          # 13:07 午餐後
        "午餐後記得吃藥，下午元氣滿滿",
        "吃完午飯了嗎？別忘記吃藥喔",
        "午後陽光正好，記得吃藥保健康",
        "中午了，吃藥讓身體好好補充能量",
        "午後微風輕拂，吃藥讓身體充滿活力",
        "用餐後別急著休息，先把藥吃了喔",
        "一顆藥，一份健康，今天也要好好照顧自己",
        "吃飽飯、吃好藥，下午精神百倍",
        "愛自己從按時吃藥開始，加油！",
        "午後是身體吸收最好的時刻，記得吃藥",
    ],
    "evening": [            # 20:07 晚餐後
        "晚餐後記得吃藥，祝平安夜晚",
        "今天辛苦了，吃完藥好好休息",
        "夜幕降臨，關心您記得吃藥喔",
        "吃過晚飯了嗎？別忘了吃藥",
        "一天將盡，記得把晚間的藥吃了",
        "辛苦工作一整天，吃藥補充元氣",
        "夜晚是身體修復的時刻，先把藥吃了",
        "晚風輕柔，願您吃完藥後好好放鬆",
        "把藥吃了，讓身體在夜裡好好休息",
        "今日事今日畢，吃完藥才能安心休息",
    ],
}

# ── 聖經經文 ─────────────────────────────────────────────────
VERSES = [
    (["你們要將一切的憂慮卸給神，", "因為祂顧念你們。"],  "彼得前書 5:7"),
    (["我靠著那加給我力量的，",       "凡事都能做。"],      "腓立比書 4:13"),
    (["耶和華是我的牧者，",           "我必不至缺乏。"],    "詩篇 23:1"),
    (["要將你的事交託耶和華，",       "祂就必成全。"],      "詩篇 37:5"),
    (["你們要休息，",                 "要知道我是神。"],    "詩篇 46:10"),
    (["神愛世人，",                   "賜下平安與盼望。"],  "約翰福音 3:16"),
    (["你不要害怕，因為我與你同在；", "不要驚惶，因為我是你的神。"], "以賽亞書 41:10"),
    (["凡勞苦擔重擔的人，",           "可以到我這裡來，我就使你們得安息。"], "馬太福音 11:28"),
    (["萬事都互相效力，",             "叫愛神的人得益處。"], "羅馬書 8:28"),
    (["我留下平安給你們，",           "我將我的平安賜給你們。"], "約翰福音 14:27"),
]

# ── 背景照片（白天：午後提醒用）────────────────────────────
BACKGROUNDS_AFTERNOON = [
    # 夕陽山景
    "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=720&h=820&fit=crop&q=80",
    # 海邊夕陽
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=720&h=820&fit=crop&q=80",
    # 晨霧草原日出
    "https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?w=720&h=820&fit=crop&q=80",
    # 高山日出雲海
    "https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=720&h=820&fit=crop&q=80",
    # 向日葵花海
    "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=720&h=820&fit=crop&q=80",
    # 金色草原夕陽
    "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=720&h=820&fit=crop&q=80",
    # 湖面晨光倒影
    "https://images.unsplash.com/photo-1501854140801-50d01698950b?w=720&h=820&fit=crop&q=80",
    # 山間湖景
    "https://images.unsplash.com/photo-1439853949212-36089c04a8a8?w=720&h=820&fit=crop&q=80",
    # 戲劇性夕陽天空
    "https://images.unsplash.com/photo-1534088568595-a066f410bcda?w=720&h=820&fit=crop&q=80",
    # 薰衣草花田
    "https://images.unsplash.com/photo-1499002238440-d264edd596ec?w=720&h=820&fit=crop&q=80",
]

# ── 背景照片（夜晚：晚間提醒用）────────────────────────────
BACKGROUNDS_EVENING = [
    # 夜晚山景星空
    "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=720&h=820&fit=crop&q=80",
    # 銀河星空
    "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=720&h=820&fit=crop&q=80",
    # 夜間山景
    "https://images.unsplash.com/photo-1536152470836-b943b246224c?w=720&h=820&fit=crop&q=80",
    # 夜晚湖景倒影
    "https://images.unsplash.com/photo-1500877015165-e1fb7f2db007?w=720&h=820&fit=crop&q=80",
    # 夜空雲層
    "https://images.unsplash.com/photo-1485470733090-0aae1788d5af?w=720&h=820&fit=crop&q=80",
    # 星空曠野
    "https://images.unsplash.com/photo-1536711614557-55e83990c679?w=720&h=820&fit=crop&q=80",
    # 夜晚森林月光
    "https://images.unsplash.com/photo-1509226704106-8a5a71ffbfa4?w=720&h=820&fit=crop&q=80",
    # 深夜海岸
    "https://images.unsplash.com/photo-1523305846158-488dedcf8629?w=720&h=820&fit=crop&q=80",
    # 夜晚城市遠景
    "https://images.unsplash.com/photo-1502790671504-542ad42d5189?w=720&h=820&fit=crop&q=80",
    # 夜間曠野星軌
    "https://images.unsplash.com/photo-1480983781676-79bfa184cc9f?w=720&h=820&fit=crop&q=80",
]

# ── 工具函式 ─────────────────────────────────────────────────
def get_font(size):
    return ImageFont.truetype(MSJH, size)

def centered(draw, text, y, font, color):
    bb = draw.textbbox((0, 0), text, font=font)
    draw.text(((W - (bb[2] - bb[0])) // 2, y), text, fill=color, font=font)

def divider(draw, y, pad=65, color=(180, 148, 60)):
    draw.line([(pad, y), (W - pad, y)], fill=color, width=1)

def detect_slot():
    h = datetime.now(ZoneInfo("Asia/Taipei")).hour
    if 10 <= h < 17: return "afternoon"
    return "evening"

# ── 主程式 ───────────────────────────────────────────────────
def generate(slot=None, out_path=None):
    if slot is None:
        slot = detect_slot()
    if out_path is None:
        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reminder.jpg")

    msg   = random.choice(MESSAGES[slot])
    verse_lines, verse_ref = random.choice(VERSES)
    bg_pool = BACKGROUNDS_AFTERNOON if slot == "afternoon" else BACKGROUNDS_EVENING
    bg_url = random.choice(bg_pool)

    # 下載背景
    bg = None
    try:
        r = requests.get(bg_url, timeout=15, allow_redirects=True)
        if r.status_code == 200 and "image" in r.headers.get("Content-Type", ""):
            bg = Image.open(io.BytesIO(r.content)).convert("RGB").resize((W, H), Image.LANCZOS)
    except Exception as e:
        print(f"背景下載失敗: {e}")

    if bg is None:
        # 暖色漸層備用
        bg = Image.new("RGB", (W, H))
        bd = ImageDraw.Draw(bg)
        for y in range(H):
            t = y / H
            bd.line([(0, y), (W, y)], fill=(int(255-t*60), int(180-t*80), int(80+t*20)))

    bg = ImageEnhance.Brightness(bg).enhance(1.08)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=1.5))

    # 半透明面板
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle([25,  25, W-25, 405], radius=20, fill=(255, 252, 240, 200))
    od.rounded_rectangle([25, 430, W-25, 693], radius=20, fill=(255, 252, 240, 192))
    img = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    GOLD  = (158, 110, 10)
    RED   = (148,  28, 28)
    NAVY  = ( 28,  48, 115)
    BROWN = (120,  78, 15)
    DARK  = ( 50,  42, 30)

    # 十字架
    cx, cy = W // 2, 52
    draw.rectangle([cx-6,  cy,     cx+6,  cy+88], fill=GOLD)
    draw.rectangle([cx-43, cy+26,  cx+43, cy+41], fill=GOLD)
    for ang in range(0, 360, 40):
        rad = math.radians(ang)
        ox, oy = cx, cy+44
        draw.line([(ox+56*math.cos(rad), oy+56*math.sin(rad)),
                   (ox+74*math.cos(rad), oy+74*math.sin(rad))], fill=GOLD, width=2)

    # 上方文字
    centered(draw, "記得吃藥喔！",  158, get_font(62), RED)
    centered(draw, msg,             240, get_font(29), BROWN)
    divider(draw, 295)
    centered(draw, "健康是神賜給我們的恩典", 312, get_font(26), DARK)
    centered(draw, "好好保重，主與你同在",   348, get_font(26), DARK)

    # 下方經文
    divider(draw, 448, pad=55)
    y = 468
    for line in verse_lines:
        centered(draw, line, y, get_font(30), NAVY)
        y += 46
    centered(draw, verse_ref, y + 4, get_font(24), NAVY)
    divider(draw, y + 46, pad=55)
    centered(draw, "願平安與你同在", y + 64, get_font(36), GOLD)

    img.save(out_path, quality=93)
    print(f"[{slot}] {msg}")
    print(f"經文: {verse_ref}")
    print(f"背景: {bg_url[40:70]}...")
    print(f"儲存: {out_path}")
    return out_path

if __name__ == "__main__":
    slot = sys.argv[1] if len(sys.argv) > 1 else None
    out  = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_reminder.jpg")
    generate(slot, out)
