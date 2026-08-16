import sys
import datetime
from pathlib import Path

# Add the scripts directory to path
scripts_dir = Path("/Users/jeffliu/my-claude-skills/must-output-brain/scripts")
sys.path.append(str(scripts_dir))
import vault_utils

id = "20260206120341"
title = "定義選擇的維度：從落後指標到領先指標"
raw_content = """引用 FB 貼文：https://www.facebook.com/share/p/16sET776s4/
核心觀點：
1. 蓋棺論定是別人的觀點，你要先定義自己。
2. 衡量選擇的好壞，在於它是否為你開啟了下一個更好的選擇。
3. 關注領先指標（每日行為）而非落後指標（累積結果，如跑量）。
4. 好的選擇能讓你成長、看見可能；錯誤的選擇如果讓你封閉，那它就是牢籠。"""

refined_content = """## 核心觀點
一個選擇的價值不取決於其當下的「正確性」，而取決於它是否具備「選擇權增強」的屬性。真正的成長源於將注意力從「落後指標」（結果）轉向「領先指標」（行為過程）。

## 四重思維轉化

### 🧠 費曼轉化 (Feynman Transformation)
評判一個選擇就像衡量一座花園。大多數人只看現在開了什麼花（落後指標/結果）。但專業的園丁看的是土壤的養分（領先指標/行為過程）。如果一個選擇讓你的土壤變肥沃了，即使現在還沒開花，它也是一個好選擇，因為它讓你有能力在未來種出任何你想要的花。

### 🎭 蒙格反轉 (Munger Inversion)
**如何讓自己陷入人生的「牢籠」？**
1. 選擇那些會讓你再也不敢做出下一個選擇的路徑（封閉性選擇）。
2. 只關注「別人的尺」，並以此來定義自己的成功與失敗。
3. 瘋狂追求落後指標（如：月跑量 180KM），即使這會摧毀你的身體（系統崩潰）。
*避坑防線*：問自己「這個選擇是讓我更自由，還是更萎縮？」。

### ⚖️ 零基思考 (Zero-Based Thinking)
假設今天沒有任何過去的負擔，我會如何定義當下的「最好選擇」？如果過去的決定（如：加入某間公司）讓你學到了足夠的知識去做出下一個更好的決定，那麼那個決定就完成了它的歷史使命。你不需要為了證明它是「對的」而繼續留在原地。

### 🚀 第二層思考 (Second-Order Thinking)
- **直接結果**：因為追求短期跑量目標而受傷或受挫。
- **連鎖反應**：
    - **思維轉向**：意識到「月跑量」是落後指標，「每週紀律」才是領先指標。
    - **評價體系重構**：不再以「蓋棺論定」的結果為重，而是以「下一個選擇的能力」為重。
    - **聲譽資產累積**：在離開的當下精確定義自己，為未來的社交網絡留下長期的正向資產。"""

tags = "#筆記/靈感 #選擇體系 #領先指標 #落後指標 #人生策略 #自我定義"
connections = [
    "20260206093147 價值觀驅動的共識：從敘事紅線到執行框架",
    "20260206114420 語言的力量：禁令 vs 限制 (規則的本質)"
]
more_connections = vault_utils.find_connections(refined_content)
connections.extend([c for c in more_connections if c not in connections])

# Create the Core Note
inbox, card = vault_utils.create_note(id, title, raw_content, refined_content, tags, connections)

# Update Daily Note with the Exercises as To-Dos
exercises_text = """
### 📝 今日練習 (來自：李柏賢 FB)
- [ ] **練習一：寫下你自己的三行墓誌銘** (定義自己，非由他人定義)
- [ ] **練習二：列出你人生中最糾結的三個選擇** (分析它們開啟了什麼、關閉了什麼)
- [ ] **練習三：找出你心中那把尺的刻度** (評估自己的價值觀量尺是否為自主選擇)
- [ ] **練習四：打電話給一個重要的人** (在「蓋棺」前表達感謝或致歉)
- [ ] **練習五：為今天的自己打一個分數，然後撕掉** (練習不被單一分數標籤化)
"""

# Find today's daily note
now = datetime.datetime.now()
date_str = now.strftime("%Y_%m_%d")
daily_note_path = vault_utils.find_daily_note(date_str)

if daily_note_path:
    with open(daily_note_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    found_ideas = False
    for i, line in enumerate(lines):
        new_lines.append(line)
        if line.strip().startswith("# Ideas"):
            found_ideas = True
            # Insert exercises right after the header/description
            insert_pos = i + 1
            if insert_pos < len(lines) and "*把腦中靈感都放在這個區域*" in lines[insert_pos]:
                insert_pos += 1
            new_lines.insert(insert_pos, exercises_text)
            
    if not found_ideas:
        new_lines.append("\n# Ideas\n" + exercises_text)

    with open(daily_note_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

print(f"Created notes:\nInbox: {inbox}\nCard: {card}\nUpdated Daily Note with Exercises.")
