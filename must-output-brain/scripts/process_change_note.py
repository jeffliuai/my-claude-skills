import sys
from pathlib import Path

# Add current dir to path
sys.path.append(str(Path(__file__).parent))
import vault_utils

raw_input = "我知道人都不喜歡改變, 但是要去了解是不願意, 能力不夠, 還是有其他的限制條件"

title = "診斷改變的阻力：意願、能力與限制"
refined = """當我們覺得別人在『抗拒改變』時，不能只用一個懶惰或頑固來解釋。我們要像醫生檢查身體一樣，分清楚問題在哪裡：
1. 是『不想要』（Desire/意願）：他看不出改變的好處，或覺得壞處更多。
2. 是『不會做』（Ability/能力）：他雖然想改，但不知道怎麼改，或手邊沒有工具。
3. 是『不能做』（Constraint/外部限制）：環境或規則讓他想動也動不了。

只有找對病因，給出的藥方（進步的方法）才會有效。"""
tags = "#筆記/靈感 #變革管理 #ADKAR #底層邏輯"

curr_id = vault_utils.get_now_id()
# Specifically searching for relevant notes in the vault
connections = vault_utils.find_connections("ADKAR 意願 能力 改變 阻力")
inbox_path, card_path = vault_utils.create_note(curr_id, title, raw_input, refined, tags, connections)

print(f"ID: {curr_id}")
print(f"Inbox: {inbox_path}")
print(f"Card: {card_path}")
print(f"Connections: {connections}")
