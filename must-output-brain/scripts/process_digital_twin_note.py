import sys
from pathlib import Path

# Add current dir to path
sys.path.append("/Users/jeffliu/my-claude-skills/must-output-brain/scripts")
import vault_utils

raw_input = """數位雙生
工作上會用到, 應該是說在規劃部門未來的產品, 
模擬真實環境, 也可能是當作一項產品, 
就是模擬5G基站可能會遇到的一些問題, 我自己也在想是否可能去模擬CPE, 這樣對於國內的網通廠來說, 吸引力更大些, 當然這會跟MTBF有相關, 但我還不是很清楚差異的地方"""

title = "數位雙生：產品規劃的『數位沙盒』"
refined = """「數位雙生」（Digital Twin）就像是在電腦裡為你的實體產品（比如 5G 基站或 CPE）做一個「超真實分身」。

### 費曼轉化（簡單來說）：
想像你要蓋一座遊樂園，與其真的花幾億元蓋好後才發現雲霄飛車轉彎太急（這就是傳統的 MTBF 硬體測試故障），不如先在電腦裡模擬出一座一模一樣的遊樂園。你可以隨意調整風速、載客量，看看什麼時候會出問題。這個「電腦裡的遊樂園」就是數位雙生。

### 核心價值：
1. **模擬未來場景**：在產品還沒真正做出來前，先在數位環境測試 5G 基站或 CPE 在各種極端狀況下的反應。
2. **超越單一指標**：MTBF（平均故障間隔）只是告訴你「多久會壞一次」，而數位雙生則是展示「為什麼會壞、怎麼壞、以及如何優化」。
3. **對網通廠的吸引力**：提供一個可預測、可調整的虛擬環境，比起單純的硬體測試，能大幅縮短研發週期並降低成本。"""

tags = "#筆記/靈感 #產品規劃 #數位雙生 #5G #CPE"

curr_id = vault_utils.get_now_id()
# Search for relevant 5G or product planning notes
connections = vault_utils.find_connections("5G 基站 CPE 產品規劃 數位雙生")
inbox_path, card_path = vault_utils.create_note(curr_id, title, raw_input, refined, tags, connections)

print(f"ID: {curr_id}")
print(f"Inbox: {inbox_path}")
print(f"Card: {card_path}")
print(f"Connections: {connections}")
