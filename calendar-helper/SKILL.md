---
name: calendar-helper
description: Google Calendar 事件管理助手 - 用一句話建立 Calendar 事件。當使用者說「建立行事曆」、「加入 Calendar」、「明天開會」、「calendar event」或描述會議時使用
allowed-tools: Bash, Read, Write
---

# Google Calendar Helper

## 功能說明

智能解析自然語言，快速建立 Google Calendar 事件。

**特色**：
- ✅ 一句話建立事件（「明天下午 3 點和 John 開會」）
- ✅ 自動解析標題、時間、地點、參加者
- ✅ 支援重複事件
- ✅ 自動發送邀請
- ✅ 缺少資訊時智能追問

---

## 執行步驟

### 步驟 1：收集使用者輸入

**使用者可能會說**：
```
範例 1：明天下午 3 點和 John 開會
範例 2：下週三 10:00-11:00 討論 Q1 計畫，會議室 A
範例 3：每週一早上 9 點 Team Standup
範例 4：後天晚上 7 點吃飯
範例 5：建立一個會議（沒有描述）
```

---

### 步驟 2：智能解析資訊

**從使用者輸入中提取**：

#### 必要資訊：
1. **標題**：從描述中提取（如「開會」、「討論 Q1 計畫」）
2. **時間**：解析時間表達式（如「明天下午 3 點」、「下週三 10:00」）

#### 選填資訊（如果有提到）：
3. **地點**：如「會議室 A」、「線上」、「總部」
4. **參加者**：如「和 John」、「John 和 Mary」
5. **結束時間**：如「10:00-11:00」
6. **重複**：如「每週一」、「每天」

---

### 步驟 3：解析時間

**時間解析對照表**：

| 表達式 | 解析結果 |
|-------|---------|
| 今天 | 當天 |
| 明天 | 當天 +1 天 |
| 後天 | 當天 +2 天 |
| 下週一/二/三... | 找到下一個該星期幾 |
| 上午/早上 X 點 | HH:00 (09:00, 10:00) |
| 下午 X 點 | 12 + X (15:00 for 3點) |
| 晚上 X 點 | 18 + X (19:00 for 7點) |
| 中午 | 12:00 |

**ISO 格式**：`YYYY-MM-DDTHH:MM:SS`

使用 Python 計算：
```python
from datetime import datetime, timedelta
import pytz

tz = pytz.timezone('Asia/Taipei')
now = datetime.now(tz)

# 明天下午 3 點
tomorrow = (now + timedelta(days=1)).replace(hour=15, minute=0, second=0)
iso_time = tomorrow.strftime('%Y-%m-%dT%H:%M:%S')
# 輸出：2026-01-14T15:00:00
```

---

### 步驟 4：顯示解析結果

顯示提取的資訊給使用者確認：
```
我理解的資訊：

📌 標題：討論 Q1 計畫
📅 時間：2026-01-14 (明天) 15:00 - 16:00
📍 地點：會議室 A
👥 參加者：John

請確認：
1. 資訊正確嗎？（回答「是」建立事件）
2. 需要修改嗎？（告訴我要改什麼）
3. 需要補充資訊嗎？（如參加者 Email、提醒時間、重複規則）
```

---

### 步驟 5：處理使用者回應

#### 情況 A：資訊正確
```
使用者：是 / 確認 / ok / yes

→ 進入步驟 6（建立事件）
```

---

#### 情況 B：需要修改
```
使用者：時間改成下午 4 點

→ 更新資訊
→ 重新顯示摘要
→ 再次確認
```

---

#### 情況 C：補充資訊
```
使用者：John 的 Email 是 john@company.com，要提前 15 分鐘提醒

→ 加入參加者和提醒
→ 重新顯示摘要
→ 再次確認
```

---

#### 情況 D：缺少必要資訊

如果無法提取標題或時間，追問：
```
使用者：建立一個事件

Claude：好的！請告訴我：
       - 什麼事件？（標題）
       - 什麼時候？（時間）
       
       或者直接描述，例如：
       「明天下午 3 點開會」

使用者：明天下午 2 點 Team Review

Claude：收到！
       📌 Team Review
       📅 明天 14:00-15:00
       
       確認建立？
```

---

### 步驟 6：建立事件

確認後，根據收集的資訊建立 JSON：

**JSON 建立規則**：
- 只加入有提取到的欄位
- `summary` 和 `start` 必須有
- 時間使用 ISO 8601 格式

**範例 1：基本事件**
```json
{
  "summary": "開會",
  "start": "2026-01-14T15:00:00"
}
```

**範例 2：完整事件**
```json
{
  "summary": "Q1 策略會議",
  "start": "2026-01-15T10:00:00",
  "end": "2026-01-15T12:00:00",
  "location": "會議室 A",
  "description": "討論 2026 Q1 目標",
  "attendees": ["john@company.com", "mary@company.com"],
  "reminders": [15, 60],
  "recurrence": "RRULE:FREQ=WEEKLY;BYDAY=MO"
}
```

執行：
```bash
cd ~/.claude/skills/calendar-helper/scripts

python3 calendar_helper.py create << 'EOF'
{建立的 JSON}
EOF
```

**重要**：
- attendees 必須是完整的 Email 地址
- 如果使用者只說「John」，需要詢問完整 Email
- 時間必須是 ISO 格式 `YYYY-MM-DDTHH:MM:SS`

---

### 步驟 7：回報結果

成功後回報：
```
✅ 事件已建立！

📌 標題：Q1 策略會議
📅 時間：2026-01-15 10:00-12:00
📍 地點：會議室 A
👥 參加者：已發送邀請給 john@company.com, mary@company.com
🔗 連結：https://calendar.google.com/...

已自動加入你的 Google Calendar
手機 app 可能需要幾分鐘同步
```

---

## 完整互動範例

### 範例 1：一句話搞定
```
使用者：明天下午 3 點開會

Claude：我理解的資訊：
       📌 標題：開會
       📅 時間：2026-01-14 15:00-16:00
       
       確認建立？需要補充資訊嗎？

使用者：是

Claude：✅ 事件已建立！
       📌 開會
       📅 2026-01-14 15:00-16:00
       🔗 https://calendar.google.com/...
```

---

### 範例 2：補充參加者
```
使用者：下週三 10 點和 John 討論專案

Claude：我理解的資訊：
       📌 標題：討論專案
       📅 時間：2026-01-22 10:00-11:00
       👥 參加者：John
       
       請問 John 的完整 Email 地址？

使用者：john@company.com

Claude：好的！
       📌 討論專案
       📅 2026-01-22 10:00-11:00
       👥 john@company.com
       
       確認建立並發送邀請？

使用者：確認

Claude：✅ 事件已建立！
       📌 討論專案
       📅 2026-01-22 10:00-11:00
       👥 已發送邀請給 john@company.com
       🔗 https://calendar.google.com/...
```

---

### 範例 3：修改資訊
```
使用者：明天下午 2 點開會

Claude：我理解的資訊：
       📌 標題：開會
       📅 時間：2026-01-14 14:00-15:00
       
       確認建立？

使用者：標題改成「產品 Demo」，地點是線上

Claude：好的，已更新：
       📌 標題：產品 Demo
       📅 時間：2026-01-14 14:00-15:00
       📍 地點：線上
       
       確認建立？

使用者：是

Claude：✅ 事件已建立！
```

---

### 範例 4：重複事件
```
使用者：每週一早上 9 點 Standup Meeting

Claude：我理解的資訊：
       📌 標題：Standup Meeting
       📅 時間：每週一 09:00-10:00
       🔄 重複：每週
       
       需要設定結束日期嗎？（如「重複到今年底」）

使用者：重複到 6 月底

Claude：好的！
       📌 Standup Meeting
       📅 每週一 09:00-10:00
       🔄 重複到 2026-06-30
       
       確認建立？

使用者：確認

Claude：✅ 重複事件已建立！
       📌 Standup Meeting
       📅 每週一 09:00-10:00
       🔄 共 26 次，直到 2026-06-30
```

---

### 範例 5：複雜事件
```
使用者：後天上午 10-12 點在大會議室和 John、Mary 討論 Q1 OKR，提前 30 分鐘提醒

Claude：我理解的資訊：
       📌 標題：討論 Q1 OKR
       📅 時間：2026-01-15 10:00-12:00
       📍 地點：大會議室
       👥 參加者：John, Mary
       ⏰ 提醒：提前 30 分鐘
       
       請問 John 和 Mary 的 Email？

使用者：john@company.com, mary@company.com

Claude：完美！
       📌 討論 Q1 OKR
       📅 2026-01-15 10:00-12:00
       📍 大會議室
       👥 john@company.com, mary@company.com
       ⏰ 提前 30 分鐘
       
       確認建立並發送邀請？

使用者：是

Claude：✅ 事件已建立！
       📌 討論 Q1 OKR
       📅 2026-01-15 10:00-12:00
       👥 已發送邀請給 2 位參加者
       🔗 https://calendar.google.com/...
```

---

## 解析提示詞（給 Claude 的內部指引）

### 標題提取

從描述中提取動作或目的：
- "開會" → 標題：開會
- "和 John 討論專案" → 標題：討論專案
- "Team Standup Meeting" → 標題：Team Standup Meeting
- "吃飯" → 標題：吃飯

如果只有時間沒有動作，標題設為「會議」或「事件」

---

### 參加者提取

關鍵字：「和」、「與」、"with"
- "和 John 開會" → 參加者：John
- "John 和 Mary" → 參加者：John, Mary
- "with John" → 參加者：John

**重要**：提取後必須詢問完整 Email

---

### 地點提取

關鍵字：「在」、「地點」、「會議室」、「線上」
- "在會議室 A" → 地點：會議室 A
- "線上開會" → 地點：線上
- "總部 3F" → 地點：總部 3F

---

### 重複規則提取

關鍵字：「每」、"every"
- "每天" → RRULE:FREQ=DAILY
- "每週" → RRULE:FREQ=WEEKLY
- "每週一" → RRULE:FREQ=WEEKLY;BYDAY=MO
- "每月" → RRULE:FREQ=MONTHLY

---

## 重複事件規則

### RRULE 格式

| 規則 | RRULE |
|------|-------|
| 每天 | `RRULE:FREQ=DAILY` |
| 每週 | `RRULE:FREQ=WEEKLY` |
| 每週一 | `RRULE:FREQ=WEEKLY;BYDAY=MO` |
| 每週一、三、五 | `RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR` |
| 每月 1 號 | `RRULE:FREQ=MONTHLY;BYMONTHDAY=1` |
| 重複 10 次 | `RRULE:FREQ=WEEKLY;COUNT=10` |
| 直到某日期 | `RRULE:FREQ=WEEKLY;UNTIL=20261231T235959Z` |

**星期縮寫**：MO, TU, WE, TH, FR, SA, SU

---

## 常見問題處理

### Q1：無法提取標題或時間
```
使用者：建立事件

Claude：請告訴我事件的標題和時間，例如：
       「明天下午 3 點開會」
```

---

### Q2：參加者沒有 Email
```
使用者：和 John 開會

Claude：請問 John 的 Email 地址？
```

---

### Q3：時間不明確
```
使用者：下週開會

Claude：請提供具體時間，例如：
       - 下週一上午 10 點
       - 下週三下午 2 點
```

---

## 注意事項

- ⚠️ 使用 Claude 的 LLM 能力解析，不依賴 Python 腳本的 parse 功能
- ⚠️ 時間必須轉換成 ISO 8601 格式：`YYYY-MM-DDTHH:MM:SS`
- ⚠️ 參加者必須是完整 Email，提取到名字後必須追問 Email
- ⚠️ 顯示摘要後必須等使用者確認才建立
- ⚠️ JSON 中只包含有提取到的欄位

---

## 費用

✅ **完全免費**

Google Calendar API 配額：
- 每天 1,000,000 次請求
- 個人使用完全在免費額度內

---

## 快速參考

### 使用方式
```
一句話描述 → 確認 → 建立
```

### 範例觸發詞

- "明天下午 3 點開會"
- "建立 Calendar 事件"
- "下週三討論專案"
- "每週一 Standup"
- "加入行事曆"
