"""
eToro XRP 網格交易機器人
Sub Portfolio: God's gift（真實帳戶）

買入邏輯：XRP 每跌 0.02，買入可用餘額 20%
賣出邏輯：XRP 每漲 0.02，賣出持倉 20%
"""
import os, uuid, json, requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

ETORO_API_KEY  = os.getenv("ETORO_API_KEY")
ETORO_USER_KEY = os.getenv("ETORO_USER_KEY")
LINE_TOKEN     = os.getenv("CHANNEL_ACCESS_TOKEN")
LINE_USER_ID   = os.getenv("USER_ID")

PNL_THRESHOLD  = 5.0   # 觸發通知的 P&L 百分比（±5%）
ALERT_COOLDOWN = 3600  # 同類型通知間隔秒數（1 小時）

BASE_URL    = "https://public-api.etoro.com/api/v1"
XRP_INST_ID = 100003  # XRP instrument ID（固定值）

# ── 網格參數 ──────────────────────────────────────────────────
BUY_START  = 1.40   # 第一格買入價
SELL_START = 1.42   # 第一格賣出價
STEP       = 0.02   # 每格間距
GRID_COUNT = 15     # 各方向最多 15 格
BUY_PCT    = 0.20   # 每格買入：可用餘額 20%
SELL_PCT   = 0.20   # 每格賣出：持倉 20%
RESET_BUFFER = 0.005  # 價格回升/回落此距離後重置格子

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xrp_state.json")

# ── API 工具 ──────────────────────────────────────────────────
def make_headers():
    return {
        "x-api-key":    ETORO_API_KEY,
        "x-user-key":   ETORO_USER_KEY,
        "x-request-id": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }

def get_xrp_price():
    r = requests.get(
        f"{BASE_URL}/market-data/instruments/rates",
        params={"instrumentIds": XRP_INST_ID},
        headers=make_headers(), timeout=10
    )
    r.raise_for_status()
    data = r.json()
    items = data if isinstance(data, list) else data.get("rates", data.get("items", data.get("instrumentRates", [])))
    if isinstance(items, list):
        for item in items:
            for field in ("rate", "ask", "bid", "lastPrice", "close", "price"):
                if field in item:
                    return float(item[field])
    elif isinstance(items, dict):
        for field in ("rate", "ask", "bid", "lastPrice", "close", "price"):
            if field in items:
                return float(items[field])
    raise ValueError(f"無法從回應中取得 XRP 價格: {data}")

def get_portfolio():
    r = requests.get(
        f"{BASE_URL}/trading/info/real/pnl",
        headers=make_headers(), timeout=10
    )
    r.raise_for_status()
    return r.json()

def buy_xrp(instrument_id, amount_usd):
    body = {
        "InstrumentID": instrument_id,
        "IsBuy": True,
        "Leverage": 1,
        "Amount": round(amount_usd, 2),
    }
    r = requests.post(
        f"{BASE_URL}/trading/execution/market-open-orders/by-amount",
        headers=make_headers(), json=body, timeout=15
    )
    r.raise_for_status()
    return r.json()

def sell_xrp_position(position_id, instrument_id, units_to_close):
    body = {
        "InstrumentId": instrument_id,
        "UnitsToDeduct": round(units_to_close, 8),
    }
    r = requests.post(
        f"{BASE_URL}/trading/execution/market-close-orders/positions/{position_id}",
        headers=make_headers(), json=body, timeout=15
    )
    r.raise_for_status()
    return r.json()

# ── LINE 推播 ─────────────────────────────────────────────────
def send_line_message(text):
    if not LINE_TOKEN or not LINE_USER_ID:
        print("  [LINE] 未設定 TOKEN 或 USER_ID，略過通知")
        return
    r = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"},
        json={"to": LINE_USER_ID, "messages": [{"type": "text", "text": text}]},
        timeout=15,
    )
    status = "OK" if r.status_code == 200 else f"FAIL ({r.status_code})"
    print(f"  [LINE] 推播: {status}")

def check_pnl_alert(xrp_positions, price, state):
    if not xrp_positions:
        return

    total_invested = sum(float(p.get("invested", p.get("amount", 0))) for p in xrp_positions)
    total_pnl      = sum(float(p.get("netProfit", p.get("pnl", 0))) for p in xrp_positions)

    if total_invested <= 0:
        return

    pnl_pct = total_pnl / total_invested * 100
    now_ts  = datetime.now(timezone.utc).timestamp()
    print(f"\n--- P&L 檢查: {pnl_pct:+.2f}% (${total_pnl:+.2f} / ${total_invested:.2f}) ---")

    last_type = state.get("last_alert_type")
    last_time = state.get("last_alert_time", 0)
    cooldown_ok = (now_ts - last_time) >= ALERT_COOLDOWN

    if pnl_pct >= PNL_THRESHOLD:
        if last_type != "profit" or cooldown_ok:
            msg = (
                f"📈 XRP 投資獲利通知\n"
                f"盈利: +{pnl_pct:.2f}%（+${total_pnl:.2f}）\n"
                f"XRP 現價: ${price:.4f}\n"
                f"投入總額: ${total_invested:.2f}"
            )
            print(f"  觸發獲利通知（≥{PNL_THRESHOLD}%）")
            send_line_message(msg)
            state["last_alert_type"] = "profit"
            state["last_alert_time"] = now_ts

    elif pnl_pct <= -PNL_THRESHOLD:
        if last_type != "loss" or cooldown_ok:
            msg = (
                f"📉 XRP 投資虧損通知\n"
                f"虧損: {pnl_pct:.2f}%（${total_pnl:.2f}）\n"
                f"XRP 現價: ${price:.4f}\n"
                f"投入總額: ${total_invested:.2f}"
            )
            print(f"  觸發虧損通知（≤-{PNL_THRESHOLD}%）")
            send_line_message(msg)
            state["last_alert_type"] = "loss"
            state["last_alert_time"] = now_ts

    else:
        if last_type is not None:
            print("  P&L 回到 ±5% 範圍內，重置通知狀態")
            state["last_alert_type"] = None
            state["last_alert_time"] = 0

# ── 狀態管理 ──────────────────────────────────────────────────
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"bought": {}, "sold": {}, "instrument_id": None}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

# ── 主邏輯 ────────────────────────────────────────────────────
def run():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*50}")
    print(f"[{now}] XRP 網格交易機器人啟動")

    state = load_state()
    inst_id = XRP_INST_ID

    # 取得目前價格
    price = get_xrp_price()
    print(f"XRP 目前價格: ${price:.4f}")

    # 取得投資組合
    portfolio = get_portfolio()
    credit        = float(portfolio.get("credit", 0))
    pending_open  = float(portfolio.get("totalMoneyOpen", 0))
    pending_close = float(portfolio.get("totalMoneyClose", 0))
    available     = credit - pending_open - pending_close
    positions     = portfolio.get("positions", [])
    xrp_positions = [p for p in positions if p.get("instrumentId") == inst_id]
    xrp_total_units = sum(float(p.get("amount", 0)) for p in xrp_positions)

    print(f"可用餘額: ${available:.2f} | XRP 持倉單位: {xrp_total_units:.4f} ({len(xrp_positions)} 筆)")

    buy_levels  = [round(BUY_START  - i * STEP, 4) for i in range(GRID_COUNT)]
    sell_levels = [round(SELL_START + i * STEP, 4) for i in range(GRID_COUNT)]

    # ── 買入 ──────────────────────────────────────────────────
    print("\n--- 檢查買入格 ---")
    for level in buy_levels:
        key = str(level)
        triggered = state["bought"].get(key, False)

        # 重置：價格回升超過格子 + buffer
        if triggered and price > level + RESET_BUFFER:
            state["bought"][key] = False
            print(f"  重置買入格 {level}（現價 {price:.4f} > {level + RESET_BUFFER:.4f}）")
            continue

        if not triggered and price <= level:
            if available < 10:
                print(f"  可用餘額不足 $10，停止買入")
                break
            amount = round(available * BUY_PCT, 2)
            print(f"  ★ 觸發買入 @ ≤{level}，下單 ${amount:.2f}")
            try:
                result = buy_xrp(inst_id, amount)
                state["bought"][key] = True
                print(f"    成功: {result}")
                # 更新餘額估算
                available -= amount
            except Exception as e:
                print(f"    失敗: {e}")

    # ── 賣出 ──────────────────────────────────────────────────
    print("\n--- 檢查賣出格 ---")
    for level in sell_levels:
        key = str(level)
        triggered = state["sold"].get(key, False)

        # 重置：價格回落超過格子 - buffer
        if triggered and price < level - RESET_BUFFER:
            state["sold"][key] = False
            print(f"  重置賣出格 {level}（現價 {price:.4f} < {level - RESET_BUFFER:.4f}）")
            continue

        if not triggered and price >= level:
            if not xrp_positions:
                print(f"  無 XRP 持倉，跳過賣出 {level}")
                continue
            print(f"  ★ 觸發賣出 @ ≥{level}")
            sold_any = False
            for pos in xrp_positions:
                pos_id    = pos["positionId"]
                pos_units = float(pos.get("amount", 0))
                units_sell = round(pos_units * SELL_PCT, 8)
                if units_sell <= 0:
                    continue
                try:
                    result = sell_xrp_position(pos_id, inst_id, units_sell)
                    print(f"    倉位 {pos_id}，賣出 {units_sell} 單位: {result}")
                    sold_any = True
                except Exception as e:
                    print(f"    倉位 {pos_id} 賣出失敗: {e}")
            if sold_any:
                state["sold"][key] = True

    # ── P&L 監控 ──────────────────────────────────────────────
    check_pnl_alert(xrp_positions, price, state)

    save_state(state)
    print("\n完成，狀態已儲存")

if __name__ == "__main__":
    run()
