import sys
from pathlib import Path

# Add scripts dir to path
sys.path.append("/Users/jeffliu/my-claude-skills/must-output-brain/scripts")
import vault_utils

raw_input = "我在想我為什麼會沒有動力去處理租屋的事情, 我是在逃避嗎? 但是這又是一個不得不面對的問題。"

title = "心理分析：解決租屋拖延的四重思維"
refined = """這是一個典型的「決策疲勞」與「心理逃避」交織的主題。租屋不僅是體力活，更涉及對「生活狀態改變」的安全感挑戰。

### 1. 費曼轉化 (Feynman - 概念理解)
**生活類比**：躲避租屋就像是「冰箱裡有個發臭的小盒子，你每天打開冰箱都聞到異味，但每次都選擇快速關上它，假裝沒看見」。逃避並不是因為你懶，而是因為那個盒子讓你感到噁心（焦慮），你下意識想保護自己遠離那種不舒服的感覺。

### 2. 蒙格反轉 (Munger - 風險防禦)
**逆向清單（如何確保這件事徹底失敗）**：
- 等到租約到期的最後一天才開始看房。
- 拒絕分析自己到底想要什麼，盲目地看每一間房。
- 每天花 5 分鐘想這件事，但不採取任何具體行動（消耗意志力而不產生產出）。
**避坑守則**：絕對不要等到「被迫決定」時才出手，因為「別無選擇」是導致租屋悲劇的主因。

### 3. 零基思考 (Zero-Based - 資源配置)
**關鍵提問**：如果我今天早上剛到這個城市，手上完全沒有住的地方（或是沒有現在這個繁瑣的租約束縛），我會如何安排我「尋找居所」的第一天？
**決策建議**：把這件事從「處理舊麻煩」重新定義為「為新的自己選一個基地」。如果重新開始，你可能更在意效率而非恐懼。

### 4. 第二層思考 (Second-Order - 連鎖反應)
**第一層（直接結果）**：今天又沒處理，獲得了短暫的心安（逃避成功）。
**第二層（ And then what?）**：
- **隱性成本**：每天都在背景消耗 10% 的大腦算力來「擔心」這件事，導致工作效率下降。
- **選擇權縮減**：好的房源被挑走，剩下的都是性價比低的，最後只能妥協。
- **情緒連鎖**：這件事會逐漸演變成對自己「執行力」的自我懷疑，進而影響到其他生活領域。"""

tags = "#筆記/靈感 #心理分析 #拖延症 #決策 #租屋 #思維工具"

curr_id = vault_utils.get_now_id()
connections = vault_utils.find_connections("心理 逃避 決策 執行力")
in_path, card_path = vault_utils.create_note(curr_id, title, raw_input, refined, tags, connections)

print(f"ID: {curr_id}")
print(f"Card: {card_path}")
print(f"Daily Note Updated.")
