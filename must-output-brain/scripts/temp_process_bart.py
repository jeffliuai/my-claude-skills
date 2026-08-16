import sys
from pathlib import Path

# Add the scripts directory to path
scripts_dir = Path("/Users/jeffliu/my-claude-skills/must-output-brain/scripts")
sys.path.append(str(scripts_dir))
import vault_utils

id = "20260206114029"
title = "BART 框架：建立心理安全感與關係邊界的四大支柱"
raw_content = """我在修修訪談雪麗老師（Sherry）的podcast中聽到BART這個重要的工具, 跟之前樊登提到育兒的方法有異曲同工之妙, 都是要建立對方的心理安全, 

BART 確實是一個源自於「組織心理學」的重要工具，用來釐清關係中的動態與界線。
雪力（Sherry）說明：
1. B - Boundary（邊界）：清楚的範圍與界限，建立心理安全。
2. A - Authority（權限）：知道自己的權利大小與權限範圍。
3. R - Role（角色）：確認站的位置與定義，達成共識。
4. T - Task（任務）：釐清現在最重要目的與優先順序。
總結來說，BART 是一個用來釐清關係、設立界線、確認權責與目標的系統化工具。"""

refined_content = """## 核心觀點
BART 是關係中的「作業系統」。透過對齊 **Boundary (邊界)**, **Authority (權限)**, **Role (角色)**, **Task (任務)**，能消除因模糊產生的「內在小劇場」，並從底層建立心理安全感。這與樊登的育兒理念（建立信任與安全感）異曲同工。

## 四重思維轉化

### 🧠 費曼轉化 (Feynman Transformation)
BART 就像是在玩一場「密室逃脫」遊戲：
- **Boundary (邊界)**：我們在多大的房間內玩？知道不會撞牆，才有安全感。
- **Authority (權限)**：誰拿著鑰匙？我有權利去碰這扇門嗎？知道權力的邊界。
- **Role (角色)**：我是解謎者還是搬運工？雙方對「角色」的定義必須一致。
- **Task (任務)**：最終目標是逃出去還是找寶藏？目標一致，協作才有效。

### 🎭 蒙格反轉 (Munger Inversion)
**如何創造一個充滿內耗、焦慮且絕對失敗的團隊或家庭？**
1. 讓**邊界 (Boundary)** 永遠隨心情變動。
2. 讓每個人都覺得自己要為「他人的情緒」負責（**權限 (Authority)** 濫用）。
3. 對「好父母」或「好員工」的表現沒有統一標準（**角色 (Role)** 定義落差）。
4. 同時給予多個衝突目標，讓大家不知道現在該忙什麼（**任務 (Task)** 模糊）。
*避坑防線*：事先講清楚規則，讓人知道邊界在哪。

### ⚖️ 零基思考 (Zero-Based Thinking)
假設今天我們要建立一個新團隊或搬進新家，沒有任何舊習。為了讓大家「不心累」，我們最先需要訂下來的四大核心協議必然是這四項。它是維繫組織運行的最小可行框架。

### 🚀 第二層思考 (Second-Order Thinking)
- **直接結果**：心理安全感建立，焦慮感降低。
- **連鎖反應**：
    - **決策成本下降**：因為權限明確，不再需要頻繁請示。
    - **情感連結加深**：角色定義清楚後，減少了「你為什麼不幫我」的委屈感。
    - **自我修復能力**：系統能在框架下實現自驅運轉，不必依賴外部不斷介入。"""

tags = "#筆記/靈感 #BART框架 #心理安全感 #組織學 #溝通心理學"
# Linking to the previous master models
connections = [
    "20260206093147 價值觀驅動的共識：從敘事紅線到執行框架",
    "20260206093049 專案執行的共識框架：聚焦核心問題"
]
more_connections = vault_utils.find_connections(refined_content)
connections.extend([c for c in more_connections if c not in connections])

inbox, card = vault_utils.create_note(id, title, raw_content, refined_content, tags, connections)
print(f"Created notes:\nInbox: {inbox}\nCard: {card}")
