# line-medicine-bot

LINE 吃藥提醒機器人，由 GitHub Actions 觸發，不依賴本地終端機。

---

## 專案架構

```
.github/workflows/
  medicine_reminder.yml   # 每天 13:00 / 20:00（台北）自動推播

send_reminder.py          # 吃藥提醒主流程：生圖 → 上傳 → 推播
generate_reminder.py      # 用 Pillow 動態生成提醒圖片

images/reminder.jpg       # 最新提醒圖片（由 Actions 上傳，供 LINE 讀取）
```

---

## GitHub Actions Secrets（需在 repo 設定）

| Secret | 用途 |
|--------|------|
| `CHANNEL_ACCESS_TOKEN` | LINE Bot Channel Access Token |
| `USER_ID` | 個人 LINE User ID（格式：`U` + 32碼） |
| `GROUP_ID` | LINE 群組 ID |
| `GITHUB_TOKEN` | 自動提供，供上傳圖片用 |

---

## 吃藥提醒流程

1. `generate_reminder.py`：Pillow 生成圖片
   - 背景：10 張 Unsplash 風景照隨機選取
   - 主訊息：依時段（午餐後 / 晚餐後）隨機選關心話語
   - 聖經經文：10 句隨機選一
2. 上傳圖片至 GitHub repo `images/reminder.jpg`（取得公開 HTTPS URL）
3. 等待 CDN 刷新（最多 15 秒）
4. LINE Push API 同時發送給個人帳號與群組

---

## Log 查看

```bash
tail -f logs/bot.log      # 即時監看
cat logs/bot.log          # 查看完整 log
```

---

## 本地手動測試

```bash
# 安裝依賴
pip install -r requirements.txt
sudo apt-get install -y fonts-noto-cjk  # Linux 中文字型

# 手動發送提醒（需 .env）
python send_reminder.py

# 生成預覽圖片
python generate_reminder.py afternoon sample.jpg
```

`.env` 格式：
```
CHANNEL_ACCESS_TOKEN=xxx
USER_ID=xxx
GROUP_ID=xxx
GITHUB_TOKEN=xxx
```

---

## 注意事項

- LINE Bot 若設有 IP 白名單，本地執行會收到 403；GitHub Actions 執行不受影響
- 吃藥提醒 workflow 執行時 `GITHUB_TOKEN` 由 Actions 自動注入，無需手動設定
