#!/usr/bin/env python3
"""
AI Card Creator - 讓 AI 創建的卡片也自動更新 Daily Note
使用方式：
    python3 ai_create_card.py --title "卡片標題" --content "深度內容" --tags "#標籤" [--raw "原始輸入"]
"""
import sys
import os
from pathlib import Path

# 添加 vault_utils 路徑
sys.path.insert(0, str(Path(__file__).parent.parent / 'must-output-brain' / 'scripts'))

from vault_utils import create_note, get_now_id
import argparse

def main():
    parser = argparse.ArgumentParser(description='Create a card and auto-update Daily Note')
    parser.add_argument('--title', required=True, help='Card title')
    parser.add_argument('--content', required=True, help='Refined content')
    parser.add_argument('--raw', default='', help='Raw content (optional)')
    parser.add_argument('--tags', default='#筆記/靈感', help='Tags (default: #筆記/靈感)')
    
    args = parser.parse_args()
    
    # 生成 ID
    card_id = get_now_id()
    
    # 使用 raw 內容，如果沒有提供則使用 refined content
    raw_content = args.raw if args.raw else args.content
    
    # 創建卡片（會自動更新 Daily Note）
    create_note(
        id=card_id,
        title=args.title,
        raw_content=raw_content,
        refined_content=args.content,
        tags=args.tags
    )
    
    print(f"✓ 已創建卡片：{card_id} {args.title}")
    print(f"✓ 已自動更新 Daily Note")
    
    return card_id

if __name__ == '__main__':
    main()
