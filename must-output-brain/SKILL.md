---
name: must-output-brain
description: |
  「一定會輸出」大腦系統 —— 將碎片想法轉換為結構化卡片，並實施費曼轉化與自動連結。
  
  觸發情境：
  (1) 用戶輸入「我有一個想法」或以此開頭。
  (2) 用戶輸入一段原始想法或邏輯不通的碎語。
  (3) 用戶輸入結構化指令。
  (4) 用戶輸入關鍵字，AI 切換為採訪者模式。
---

# Must Output Brain

## AI 使用協議 (Interaction Protocol)

**當接收到用戶輸入時，AI 必須：**

1. **識別輸入模式**：
    - **觸發字**：如用戶輸入「我有一個想法」或以此開頭，則根據後續內容長度決定進入「碎語模式」(2-5) 或「採訪模式」。
    - **短文字/邏輯不通**：直接進行流程 2-5。
    - **結構化指令**：按指令執行後進行流程 2-5。
    - **關鍵字**：啟動「採訪者模式」。

2. **四重思維轉化 (The Quadruple-Thought Transformation)**：
    - **費曼轉化 (Feynman - 概念理解)**：用白話與類比翻譯專業概念。
    - **蒙格反轉 (Munger - 風險防禦)**：列出「如何絕對會失敗」清單與避坑防線。
    - **零基思考 (Zero-Based - 資源配置)**：假設現狀不存在，重新評估投入的必要性與沉沒成本。
    - **第二層思考 (Second-Order - 連鎖反應)**：分析直接結果之後的連鎖反應（And then what?），預測長期影響。

3. **執行自動化腳本 (`vault_utils.py`)**：
    - 生成時間 ID (`YYYYMMDDHHMM`)。
    - 在 `000 INBOX` 建立 `ID Raw.md`（保存原始輸入）。
    - 在 `002 CARDS` 建立 `ID Title.md`（保存轉化後的內容）。
    - 掃描庫中 3-5 個相關筆記並生成 `[[Connections]]`。

4. **套用卡片範本**：
    - 使用 YAML frontmatter (uid, created, tags)。
    - 結構包含：`# 標題`, `## 內容`, `---`, `## 🔗 連結`。

5. **回報結果**：
    - 提供產出卡片的內容預覽。
    - 確認 Inbox 與 Cards 的存檔成功。

6. **同步 Telegram 訊息 (Selective Sync)**：
    - 當接收到「在telegram上提到」、「同步 Telegram」或「處理 Telegram 訊息」指令時。
    - 讀取 `/Users/jeffliu/Documents/A05_Obsidian Vault/000 INBOX/.tg_pending.json`。
    - **規則 1 (分析模式)**：若訊息包含「我有一個想法」或以此開頭，則將其視為「原始輸入」丟入「四重思維轉化」流程 (步驟 2-5)。
    - **規則 2 (隨記模式)**：若訊息無特定關鍵字，則調用 `scripts/vault_utils.py` 將其直接以 `[時間] (TG) 內容` 格式存入當天 Daily Note 的「# I. 每日活動 / 雜記」區塊中。
    - 處理完後將該訊息標記為 `processed: true`。

7. **管理背景監聽服務**：
    - **「啟動背景監聽」**：執行 `scripts/manage_service.py enable`（啟動永久自動監聽）。
    - **「關閉背景監聽」**：執行 `scripts/manage_service.py disable`（移除自動啟動設定）。
    - **「監聽狀態」**：執行 `scripts/manage_service.py status`。

## 生態系元件
- `scripts/vault_utils.py`: 核心工具（ID, 搜索, 存檔）。
- `scripts/tg_listener.py`: Telegram 接收器（需在背景執行）。
- `scripts/tg_token.txt`: 存放 Bot Token。

## 設定步驟 (Setup Telegram)
1. 透過 @BotFather 申請一個 Bot。
2. 將 Token 貼入 `scripts/tg_token.txt`。
3. 在終端機執行：`python3 scripts/tg_listener.py`。
4. 開始對 Bot 說話（或用語音轉文字）。
