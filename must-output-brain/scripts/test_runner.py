import sys
from pathlib import Path

# Add current dir to path
sys.path.append(str(Path(__file__).parent))
import vault_utils

# 1. Simulate Raw Input
raw_input = "我覺得知識複利很重要，不只是讀書，還要整理。長期主義也是，不要急著變現。費曼轉化就是講給別人聽。"

# 2. AI Processing (Simulated)
title = "打造知識複利：長期主義與費曼轉化"
refined = "知識的價值不在於你讀了多少，而在於你留下了多少。真正的學習要靠整理與長期的積累，就像複利一樣，時間越長價值越高。而檢驗自己是否真的學會，最好的方式就是『費曼轉化』：嘗試用最簡單的話講給別人聽，如果你能讓國中生也聽懂，那才算真正內化了。"
tags = "#筆記/靈感 #學習方法"

# 3. Automation
curr_id = vault_utils.get_now_id()
connections = vault_utils.find_connections(refined)
in_path, card_path = vault_utils.create_note(curr_id, title, raw_input, refined, tags, connections)

print(f"Created Inbox: {in_path}")
print(f"Created Card: {card_path}")
print(f"Connections found: {connections}")
