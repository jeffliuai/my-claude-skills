import sys
from pathlib import Path

# Add the scripts directory to path
scripts_dir = Path("/Users/jeffliu/my-claude-skills/must-output-brain/scripts")
sys.path.append(str(scripts_dir))
import vault_utils

id = "20260207090314"
title = "心理系統動力學：從 B=f(P,E) 到改變的免疫系統"
raw_content = """整理修修與雪力老師對話的重點摘要：
1. B = f(P, E) 公式 (Lewin’s Equation)：行為（Behavior）是個人（Person）與環境（Environment）的函數。
2. 心理恆溫器 (Homeostasis)：身心有恆溫機制，太劇烈的改變會觸發保護機制強行拉回原點。
3. 改變的免疫系統 (Immunity to Change)：Kegan 理論。無法改變是因為內有「競爭性承諾」與「巨大的假設」。
4. 結語：人生卡關往往不是油門踩不夠，而是煞車踩太死。"""

refined_content = """## 核心模型：心理 X 光 (The Psychological X-Ray)
透過這套框架，我們可以穿透行為的表象，看見動力系統中的「煞車」與「油門」。

### 1. 外部力學：B = f(P, E)
行為（Behavior）不是獨立存在的，而是**個人 (Person)** 與 **環境 (Environment)** 的共同作用。
- **洞察**：當行為出問題時，別急著怪罪個人。更高效的解法往往是調整「環境」這個變數（例如 BART 框架中的邊界與角色定義）。

### 2. 生態平衡：心理恆溫器 (Homeostatic Setting)
大腦厭惡劇烈波動。
- **洞察**：快速的「神級進化」通常會觸發崩潰機制。真正的改變需要「微調設定值」，讓潛意識在感到安全的前提下慢慢挪動。

### 3. 內部煞車：改變的免疫系統 (Immunity to Change)
這套由 Robert Kegan 提出的框架解釋了「想改卻改不掉」的本質。
- **油門**：顯性目標（我想減肥）。
- **煞車**：隱性承諾（我承諾要以吃宵夜來愛自己）。
- **地基**：巨大假設（如果不吃宵夜，我就不愛自己）。
- **洞察**：不鬆開煞車（挑戰假設），油門踩得再猛也只是空轉與自責。

---

## 四重思維轉化

### 🧠 費曼轉化 (Feynman Transformation)
這就像是開車上山。**B=f(P,E)** 告訴我們，開不動可能是因為車子舊（P），也可能是因為坡太陡（E）。**心理恆溫器** 是車上的限速器，你一下子想開到 200，系統會自動斷油。而 **改變的免疫系統** 則是有人一邊踩著油門，一邊卻死死拉著手煞車。要上山，你不一定要換新車，可能只需要放掉手煞車並修好路面（環境）。

### 🎭 蒙格反轉 (Munger Inversion)
**如何確保自己永遠無法改變且陷入終身自責？**
1. 發生問題時，100% 歸咎於自己意志力不足（只看 P，忽略 E）。
2. 每次元旦都訂下「徹底脫胎換骨」的計畫（觸發恆溫器強烈反彈）。
3. 忽視內心的「微弱聲音」，不承認自己其實「不想改」（隱藏承諾）。
*避坑防線*：先做「免疫地圖」掃描，看清手煞車拉在哪裡。

### ⚖️ 零基思考 (Zero-Based Thinking)
假設我們不考慮「我是個懶惰的人」這個既定標籤（歸零 P），單純看環境（E），有哪些外部阻力是可以被移除的？很多時候，移除一顆阻礙的石頭，比培養一個大力士更簡單。

### 🚀 第二層思考 (Second-Order Thinking)
- **直接結果**：減少自我攻擊，獲得短暫平靜。
- **連鎖反應**：
    - **理解力的飛躍**：能看穿他人的行為（如同事的擺爛）可能是環境（E）的系統性問題。
    - **策略重心的轉移**：從「訓練意志力」轉向「設計環境」與「解構假設」。
    - **長期的穩定性**：因為順應了恆溫機制，改變雖然慢，但不會復胖。"""

tags = "#筆記/靈感 #心理學 #系統思考 #改變的免疫系統 #BART框架"
connections = [
    "20260206114029 BART 框架：建立心理安全感與關係邊界的四大支柱",
    "20260206093147 價值觀驅動的共識：從敘事紅線到執行框架",
    "20260206120341 定義選擇的維度：從落後指標到領先指標"
]
more_connections = vault_utils.find_connections(refined_content)
connections.extend([c for c in more_connections if c not in connections])

inbox, card = vault_utils.create_note(id, title, raw_content, refined_content, tags, connections)
print(f"Created notes:\nInbox: {inbox}\nCard: {card}")
