import sys
from pathlib import Path

# Add scripts dir to path
sys.path.append("/Users/jeffliu/my-claude-skills/must-output-brain/scripts")
import vault_utils

raw_input = """我有一個想法, 我覺得領導力不管是用在團隊, 面對同事,或是家裡, 面對女兒, 都有類似的做法, 
最主要就是要以身作則, 不要亂發脾氣, 不是說不能有情緒, 但是身為領導者的我, 不要隨著女兒的情緒起舞, 而是要引導他們,"""

title = "跨場域的領導力：做一個不被情緒帶走的『定海神針』"
refined = """不論是在公司帶團隊，還是在家裡教女兒，領導力的本質其實是同一件事：**「穩住自己，才能引導他人」。**

### 費曼轉化（生活類比）：
想像你是一艘大船的船長。當海浪（女兒的情緒或同事的壓力）波濤洶湧時，如果船長也跟著慌亂尖叫，那整艘船就會失控。領導者不是不能有感覺，而是要做那顆穩重的「大錨」。當對方的情緒在大吵大鬧時，如果你能保持冷靜，你就給了對方一個可以依靠的基準點。

### 核心原則：
1. **以身作則（Modeling）**：你想讓對方冷靜，你得先示範什麼是冷靜。
2. **情緒解耦**：不隨著對方的情緒「起舞」。對方的憤怒是他的，你的穩定是你的。
3. **從反映轉向引導**：當你不再只是對情緒做出「反應」時，你才真正開始「引導」。"""

tags = "#筆記/靈感 #領導力 #親子溝通 #情緒管理 #以身作則"

curr_id = vault_utils.get_now_id()
# Search for related notes: leadership, daughter/child, emotions, modeling
connections = vault_utils.find_connections("領導力 親子 溝通 情緒 以身作則 引導")
inbox_path, card_path = vault_utils.create_note(curr_id, title, raw_input, refined, tags, connections)

print(f"ID: {curr_id}")
print(f"Inbox: {inbox_path}")
print(f"Card: {card_path}")
print(f"Connections: {connections}")
