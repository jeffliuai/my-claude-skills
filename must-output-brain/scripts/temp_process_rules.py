import sys
from pathlib import Path

# Add the scripts directory to path
scripts_dir = Path("/Users/jeffliu/my-claude-skills/must-output-brain/scripts")
sys.path.append(str(scripts_dir))
import vault_utils

id = "20260206114420"
title = "語言的力量：禁令 vs 限制 (規則的本質)"
raw_content = """引用 FB 貼文：https://www.facebook.com/share/p/17u8Tox7k7/
核心觀點：
1. 禁令 (Prohibition)：權力的展現，封閉思考，觸發對抗。「不可以！」
2. 限制/邊界 (Restriction/Limit)：事實的描述，開啟思考，建立安全感。「那是熱的，會燙到喔。」
這與樊登提到的育兒方法一致：用「規則」取代「規矩」，用「事實」取代「命令」。」"""

refined_content = """## 核心觀點
溝通的成敗取決於語言將對方定位為「被命令的客體」還是「被信任的核心」。**禁令** (Prohibition) 關閉大腦，引發權力博弈；**限制/邊界** (Restriction) 打開大腦，建立基於事實的邏輯理解與心理安全感。

## 四重思維轉化

### 🧠 費曼轉化 (Feynman Transformation)
「禁令」就像是迷宮裡的死胡同，牆上寫著「不准過」，你只會感到沮喪或想翻牆。「限制」則是迷宮裡的地圖，告示牌寫著「前方施工中」，你理解了路徑受阻的原因，會主動尋找替代路徑。地圖（限制）比圍牆（禁令）更能帶來行動的自由。

### 🎭 蒙格反轉 (Munger Inversion)
**如何讓孩子或部屬絕對不聽你的話？**
1. 所有的要求都以「不准」、「不可以」開頭，且不給理由。
2. 建立隨個人情緒波動的「隱形規矩」。
3. 將對方的行為直接貼上終局性標籤（如「你失敗了」而非「這遇到了挫折」）。
*避坑防線*：區分「規矩」（權威）與「規則」（共識/事實）。

### ⚖️ 零基思考 (Zero-Based Thinking)
如果我們移除管理中的所有「權力威壓」，只留下「客觀限制」，這個系統是否還能運作？如果不能，說明目前的管理極度依賴行政霸權，而非價值共識。真正的領導力源於讓對方「自願」接受環境的物理限制。

### 🚀 第二層思考 (Second-Order Thinking)
- **直接結果**：當下的服從或衝突減少。
- **連鎖反應**：
    - **思考能力的提升**：對方開始學會分析原因，而非觀察你的臉色。
    - **心理安全感的內化**：因為邊界清晰且固定，對方敢於在安全區內最大化自由。
    - **權力成本的降低**：當規則成為共識，監督成本會降至最低。
    - **身份認同的轉變**：對方從「接受命令的人」轉變為「遵守規則的專業人士」。"""

tags = "#筆記/靈感 #溝通心理學 #語言的力量 #心理安全感 #BART框架"
# Linking back to BART and the Consensus Master model
connections = [
    "20260206114029 BART 框架：建立心理安全感與關係邊界的四大支柱",
    "20260206093147 價值觀驅動的共識：從敘事紅線到執行框架",
    "20260206093049 專案執行的共識框架：聚焦核心問題"
]
more_connections = vault_utils.find_connections(refined_content)
connections.extend([c for c in more_connections if c not in connections])

inbox, card = vault_utils.create_note(id, title, raw_content, refined_content, tags, connections)
print(f"Created notes:\nInbox: {inbox}\nCard: {card}")
