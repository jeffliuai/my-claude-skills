import sys
from pathlib import Path

# Add scripts directory
scripts_dir = Path("/Users/jeffliu/my-claude-skills/must-output-brain/scripts")
sys.path.append(str(scripts_dir))
import vault_utils

# Data
cycle = "2026Q1"
week_num = 1
date_range = "02/02-02/08"
score = 78.6
status = "已執行"
note = "慢跑與靈感滿分；貼文與 AI 案例待加強"

# Update 12週執行報告_2026Q1.md
report_path = Path("/Users/jeffliu/Documents/A05_Obsidian Vault/003 CALENDAR/12週執行報告_2026Q1.md")
if report_path.exists():
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update table row
    # Old row: | Week 1 | 02/02-02/08 | - | 待執行 | |
    old_row = "| Week 1 | 02/02-02/08 | - | 待執行 | |"
    new_row = f"| Week 1 | {date_range} | {score}% | {status} | {note} |"
    content = content.replace(old_row, new_row)
    
    # Update summary counts (assuming 0/X to start)
    # Goal 1: Content (0/2 completed this week)
    content = content.replace("進度：0/24 (0%)", "進度：0/24 (0%)") # No change to completed count
    # Goal 2: Jogging (4 completed this week)
    content = content.replace("進度：0/48 (0%)", "進度：4/48 (8%)")
    content = content.replace("總里程：0/240 公里", "總里程：20/240 公里")
    # Goal 3: AI Case (0 completed this week)
    content = content.replace("進度：0/3 (0%)", "進度：0/3 (0%)")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated {report_path}")

# Create Weekly Review Note
review_id = "20260209105932"
review_title = "Week 6 週復盤暨 12 週計畫 Week 1 報告"
raw_content = f"Week 1 (Feb 2 - Feb 8) Progress: {score}%"
refined_content = f"""## 📊 12 週計畫執行數據 (Week 1)
- **總執行率**：{score}% (11/14)
- **戰術達成情況**：
    - 戰術 1-3 (每日靈感記錄)：7/7 [x]
    - 戰術 2-1 (每週慢跑 4 次)：4/4 [x]
    - 戰術 1-1 (週二短貼文)：0/1 [ ]
    - 戰術 1-2 (週五主貼文)：0/1 [ ]
    - 策略專案 1-1 (AI 案例 #1)：0/1 [ ]

## 🔍 週 AAR (After Action Review)

### 1. What went well? (做得好的)
- **運動習慣極致穩定**：成功完成 4 次慢跑，時速維持在 11.5 左右，展現了這半年累積的底力。
- **高頻靈感採集**：透過 Telegram 同步，每天都有記錄靈感，特別是關於「變革管理」、「B=f(P,E)」與「BART 框架」的深度反思。

### 2. What could be better? (待改進的)
- **內容輸出卡關**：雖然靈感很多，但尚未轉化為對外的臉書貼文。可能是因為對「完美度」有隱性要求，或未預留專屬的「排版與發佈」時間塊。
- **AI 案例延遲**：本週應完成的第一個 AI 案例（策略專案）尚未動工。

### 3. Key Learning (核心洞察)
- **「環境優先」的實踐**：在 2/7 的反思中提到，變革應該重點改變「環境(E)」而非「人(P)」。對於內容產出，是否也需要調整我的環境？例如：設定一個「不關機就不能睡覺」的發文倒數。

## 🚀 下週 Action Items
- [ ] **補課行動**：將本週整理的「心理系統動力學」或「BART 框架」整理成一篇深度文章發布（補回 Week 1 欠帳）。
- [ ] **環境微調**：嘗試「照書實作」，週四晚上 20:30 強制進入「策略時間塊」進行排版工作。
"""

tags = "#復盤 #12週計畫 #自我成長 #執行力"
connections = ["12週執行報告_2026Q1", "12週計畫_2026Q1", "20260207091216 變革者的槓桿：環境優先與「照書實作」的執行學"]

# we want this in CALENDAR/2026-W07 (if current week is W07) or just CALENDAR
# Let's find today's folder
week_folder = vault_utils.get_week_folder_name()
save_dir = vault_utils.CALENDAR_DIR / week_folder
save_dir.mkdir(parents=True, exist_ok=True)
review_file = save_dir / f"{review_title}.md"

# Use create_note but manually place or just use it as a card? 
# The user might prefer it in CALENDAR. 
# Let's use create_note to get the processing (s2t) and then move it if needed, or just create it directly.
# Given it's a review, putting it in 002 CARDS is also fine as it's a "knowledge object" of the week.
# But existing reviews are in 003 CALENDAR.

inbox, card = vault_utils.create_note(review_id, review_title, raw_content, refined_content, tags, connections)

# Now move the card to CALENDAR
card_path = Path(card)
target_path = save_dir / card_path.name
import os
os.rename(card_path, target_path)

print(f"Created review report at: {target_path}")
