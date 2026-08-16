import sys
from pathlib import Path

# Add the scripts directory to path
scripts_dir = Path("/Users/jeffliu/my-claude-skills/must-output-brain/scripts")
sys.path.append(str(scripts_dir))
import vault_utils

id = "20260206093049"
title = "專案執行的共識框架：聚焦核心問題"
raw_content = """針對 @20260206091530 敘事優先順序與價值觀紅線 這張卡片, 讓我聯想到再執行專案或是解決客人的問題時, 我所採用的方法很類似, 要先找出會議或是要解決的問題, 將大家的注意力都放在上面, 也算是取得大家的共識, 或是一種框架,"""

refined_content = """## 核心觀點
在專案執行與解決客訴時，最高優先級的行動不是「提供解決方案」，而是「框定問題邊界」。通過聚焦核心問題來取得共識，建立一個讓所有參與者都在同一個維度思考的「共識框架」。

## 四重思維轉化

### 🧠 費曼轉化 (Feynman Transformation)
這就像是大家聚在一起拼圖。如果每個人心裡想的「成品圖」都不一樣（溝通目標不一），那拼圖永遠拼不完。與其急著動手拿零件，不如先把那一張「成品參考圖」投影在大螢幕上。這張參考圖就是「核心問題」，當所有人都看著同一張圖時，合作才真正開始。

### 🎭 蒙格反轉 (Munger Inversion)
**如何讓一個專案會議徹底失敗並激怒客人？**
1. 讓每個人帶著不同的假設進入會議，且不進行對齊。
2. 讓會議在沒有定義「成功標準」的情況下開始。
3. 對於客人的情緒或表面需求過度反應，而忽略了底層的系統性問題。
*避坑防線*：會議前 10 分鐘，必須確認「我們今天聚在這裡是為了達成什麼共識？」。

### ⚖️ 零基思考 (Zero-Based Thinking)
假設我們還沒開始這個專案，現在客人的問題擺在面前。我們是否應該直接沿用舊有的 SOP？不，零基思考要求我們問：如果今天要用最少資源解決問題，目前的「共識框架」是否過於臃腫？是否抓到了那個「只要解決了它，其他問題都會消失」的槓桿點？

### 🚀 第二層思考 (Second-Order Thinking)
- **直接結果**：會議效率提高，客人感到被理解。
- **連鎖反應**：
    - 建立專業度（Authoritative Presence）：專家不是懂答案，而是懂問問題。
    - 減少重工：共識框架避免了後續因理解落差導致的修補。
    - 沉澱組織資產：這種「聚焦框架」可以被模組化，成為團隊的核心競爭力。"""

tags = "#筆記/靈感 #專案管理 #共識框架 #解決問題"
# Explicitly add the link to the related card
connections = ["20260206091530 敘事優先順序與價值觀紅線"]
more_connections = vault_utils.find_connections(refined_content)
connections.extend([c for c in more_connections if c not in connections])

inbox, card = vault_utils.create_note(id, title, raw_content, refined_content, tags, connections)
print(f"Created notes:\nInbox: {inbox}\nCard: {card}")
