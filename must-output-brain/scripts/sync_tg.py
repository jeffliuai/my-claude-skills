#!/usr/bin/env python3
import sys
import re
from pathlib import Path

# Add current dir to path
sys.path.append(str(Path(__file__).parent))
import robust_sync_tg

if __name__ == "__main__":
    r1, r2, r_url = robust_sync_tg.process_messages()
    print(f"Sync Result: Rule 1 ({r1} ideas), Rule 2 ({r2} logs), Rule 3 ({r_url} URLs)")
    if r_url > 0:
        print(f"\n💡 提醒：發現 {r_url} 個新網址！請記得在 Antigravity 中執行 `/process-tg-urls` 以自動爬取內容並製作卡片。")
