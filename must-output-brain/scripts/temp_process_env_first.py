import sys
from pathlib import Path

# Add the scripts directory to path
scripts_dir = Path("/Users/jeffliu/my-claude-skills/must-output-brain/scripts")
sys.path.append(str(scripts_dir))
import vault_utils

id = "20260207091216"
title = "變革者的槓桿：環境優先與「照書實作」的執行學"
raw_content = """核心概念：
1. B=f(P,E) 的實踐：變革的重點應放在改變「環境 (E)」，而非試圖強行改變「人 (P)」。
2. 照書養/照書實作：以知識為藍本先行啟動（如同樊登育兒），再依據當下環境與反饋進行動態調整。
3. 把知識實作化：實作之後的微調才是真正的學習本質。"""

refined_content = """## 核心觀點
真正的變革槓桿在於「環境設計」而非「意志對抗」。透過 B=f(P,E) 公式，變革者應將 80% 的精力投入環境變數的調整。同時，藉由「先行實作、後續微調」（照書實作）的策略，能大幅降低啟動成本並在回饋中完成知識的本土化。

## 四重思維轉化

### 🧠 費曼轉化 (Feynman Transformation)
改變一個人就像教魚爬樹。如果你只盯著魚（個人 P），你會覺得它很笨、不努力。但如果你把水池換成海洋（環境 E），它自然就能游出驚人的速度。與其教育魚如何「像鳥一樣生活」，不如幫它打造一個讓它本能就能發揮的「好水域（系統環境）」。

### 🎭 蒙格反轉 (Munger Inversion)
**如何確保一項變革或新習慣百分之百失敗？**
1. 將失敗的原因全部歸咎於參與者的「態度不端正」或「能力不足」。
2. 在完全不改變物理與制度環境的前提下，要求大家改變行為。
3. 拒絕現成的成熟方案（書本知識），堅持從零開始「純原創」摸索，增加無謂的啟動阻力。
*避坑防線*：先改環境，隨後引入成熟範式（書本/SOP）作為啟動地基。

### ⚖️ 零基思考 (Zero-Based Thinking)
如果我們不預設某人是「不愛運動」或「家教不好」，而是假設每個人都像一台「完全由環境驅動」的機器，我們會如何重新配置桌子的擺放、溝通的流程或家裡的動線？這種「環境決定論」的極端思考，往往能找到被忽略的低成本槓桿。

### 🚀 第二層思考 (Second-Order Thinking)
- **直接結果**：新方案快速上線，行為開始發生變化。
- **連鎖反應**：
    - **知識實作化**：書本知識不再是死知識，而是在與環境碰撞中產生的「活實踐」。
    - **阻力衰減**：因為環境順手了，行為變得「毫不費力」，恆溫器的反彈力降至最低。
    - **組織文化重塑**：當環境持續支持某種行為，這種行為最終會沉澱為文化（BART 框架的角色深化）。"""

tags = "#筆記/靈感 #變革管理 #環境設計 #照書實作 #實踐轉化 #BART框架"
connections = [
    "20260207090314 心理系統動力學：從 B=f(P,E) 到改變的免疫系統",
    "20260206114029 BART 框架：建立心理安全感與關係邊界的四大支柱",
    "20260130102600 規則設計的本質：從控制工具到價值觀載體"
]
more_connections = vault_utils.find_connections(refined_content)
connections.extend([c for c in more_connections if c not in connections])

inbox, card = vault_utils.create_note(id, title, raw_content, refined_content, tags, connections)
print(f"Created notes:\nInbox: {inbox}\nCard: {card}")
