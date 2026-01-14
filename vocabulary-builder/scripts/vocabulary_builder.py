#!/usr/bin/env python3
"""
Vocabulary Builder - C1/C2 單字學習文章生成器
支援：
1. 從最近文章隨機挑選單字
2. 避免重複組合
3. 自動追蹤使用歷史
"""

import os
import sys
import json
import re
import random
from datetime import datetime
from pathlib import Path

class VocabularyBuilder:
    """單字學習內容生成器"""
    
    def __init__(self, output_dir="output"):
        self.output_dir = Path(output_dir)
        self.articles_dir = self.output_dir / "Articles"
        self.words_dir = self.output_dir / "Words"
        self.metadata_dir = self.output_dir / ".metadata"
        self.combinations_file = self.metadata_dir / "word_combinations.json"
        
        # 建立輸出資料夾
        self.articles_dir.mkdir(parents=True, exist_ok=True)
        self.words_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # 載入已使用的組合
        self.used_combinations = self._load_combinations()
    
    def _load_combinations(self):
        """載入已使用的單字組合"""
        if self.combinations_file.exists():
            with open(self.combinations_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _save_combinations(self):
        """儲存已使用的單字組合"""
        with open(self.combinations_file, 'w', encoding='utf-8') as f:
            json.dump(self.used_combinations, separators=(',', ':'), ensure_ascii=False, indent=2)
    
    def get_latest_article(self):
        """找到最近一次的文章"""
        articles = list(self.articles_dir.glob("*.md"))
        if not articles:
            return None
        
        # 按修改時間排序，取最新的
        latest = max(articles, key=lambda p: p.stat().st_mtime)
        return latest
    
    def extract_words_from_article(self, article_path):
        """從文章中提取 [[單字]] 清單"""
        with open(article_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用正則表達式提取 [[word]]
        pattern = r'\[\[([^\]]+)\]\]'
        words = re.findall(pattern, content)
        
        # 去重並排序
        unique_words = sorted(set(words))
        return unique_words
    
    def check_combination_used(self, word1, word2):
        """檢查單字組合是否已使用過"""
        combo = tuple(sorted([word1.lower(), word2.lower()]))
        return combo in [tuple(sorted([c['word1'].lower(), c['word2'].lower()])) 
                        for c in self.used_combinations]
    
    def pick_random_words(self, word_list, max_attempts=10):
        """
        隨機挑選兩個單字（避免重複組合）
        
        Args:
            word_list: 可用單字清單
            max_attempts: 最大嘗試次數
            
        Returns:
            (word1, word2) 或 None（如果找不到未用過的組合）
        """
        if len(word_list) < 2:
            return None
        
        attempts = 0
        while attempts < max_attempts:
            # 隨機挑選兩個不同的單字
            word1, word2 = random.sample(word_list, 2)
            
            # 檢查是否已使用過
            if not self.check_combination_used(word1, word2):
                return (word1, word2)
            
            attempts += 1
        
        # 如果所有組合都用過，返回 None
        return None
    
    def track_word_combination(self, word1, word2, topic):
        """追蹤已使用的單字組合"""
        combo = {
            'word1': word1,
            'word2': word2,
            'topic': topic,
            'date': datetime.now().strftime("%Y-%m-%d"),
            'timestamp': datetime.now().isoformat()
        }
        self.used_combinations.append(combo)
        self._save_combinations()
    
    def generate_article_filename(self):
        """生成主文檔檔名（日期格式）"""
        today = datetime.now().strftime("%Y-%m-%d")
        return f"{today}.md"
    
    def generate_word_filename(self, word):
        """生成單字檔案名稱"""
        return f"{word.lower()}.md"
    
    def check_word_exists(self, word):
        """檢查單字檔案是否已存在"""
        word_file = self.words_dir / self.generate_word_filename(word)
        return word_file.exists()
    
    def create_main_article(self, topic, word1, word2, content, word_list):
        """建立主文檔"""
        filename = self.generate_article_filename()
        filepath = self.articles_dir / filename
        
        # 生成單字表格
        table = self.generate_word_table(word_list)
        
        article_content = f"""# {datetime.now().strftime("%Y-%m-%d")}

## 主題：{topic}

{content}

---

## 今日單字清單

{table}

---

*生成時間：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
*起始單字：{word1}, {word2}*
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(article_content)
        
        # 追蹤單字組合
        self.track_word_combination(word1, word2, topic)
        
        return filepath
    
    def generate_word_table(self, word_list):
        """生成單字表格"""
        table = """| 單字 | 詞性 | 中文意思 | 難度 |
|------|------|---------|------|
"""
        for word_info in word_list:
            word = word_info['word']
            pos = word_info.get('pos', 'adj./v.')
            meaning = word_info.get('meaning', '（待補充）')
            level = word_info.get('level', 'C1')
            table += f"| [[{word}]] | {pos} | {meaning} | {level} |\n"
        
        return table
    
    def create_word_file(self, word_data):
        """建立單字 md 檔案"""
        word = word_data['word']
        filename = self.generate_word_filename(word)
        filepath = self.words_dir / filename
        
        # 檢查檔案是否已存在
        if filepath.exists():
            return None  # 跳過
        
        # 生成單字內容
        content = self.generate_word_content(word_data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath
    
    def generate_word_content(self, word_data):
        """生成單字檔案內容"""
        word = word_data['word']
        pronunciation = word_data.get('pronunciation', '/wɜːrd/')
        
        # Cambridge Dictionary 發音連結
        audio_link = f"https://dictionary.cambridge.org/pronunciation/english/{word.lower()}"
        
        content = f"""# {word}

🔊 [發音]({audio_link})

## Form（形式）

### 字根字首
{word_data.get('etymology', '- 待補充字根資訊')}

### 相關字族
{word_data.get('word_family', '- 待補充相關字')}

### 發音
- IPA: {pronunciation}

### 諧音記憶
{word_data.get('mnemonic', '- 待補充諧音記憶')}

---

## Meaning（意義）

### 定義
{word_data.get('definition', '待補充定義')}

### 隱含義（Connotation）
{word_data.get('connotation', '- 待補充隱含義')}

### 近義字
{word_data.get('synonyms', '- 待補充近義字')}

### 反義字
{word_data.get('antonyms', '- 待補充反義字')}

---

## Use（用法）

### 常見搭配詞
{word_data.get('collocations', '- 待補充搭配詞')}

### 使用情境
{word_data.get('contexts', '- 待補充使用情境')}

### 例句

{word_data.get('examples', '- 待補充例句')}

---

*建立日期：{datetime.now().strftime("%Y-%m-%d")}*
*狀態：📝 待複習*
"""
        return content

def main():
    """主函數"""
    if len(sys.argv) < 2:
        print(json.dumps({
            'error': '請提供 JSON 輸入',
            'usage': 'echo \'{"mode": "manual|random", ...}\' | python3 vocabulary_builder.py'
        }))
        sys.exit(1)
    
    # 從 stdin 讀取 JSON
    try:
        data = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        print(json.dumps({'error': f'JSON 解析錯誤: {str(e)}'}))
        sys.exit(1)
    
    # 初始化
    output_dir = data.get('output_dir', '../output')
    builder = VocabularyBuilder(output_dir=output_dir)
    
    mode = data.get('mode', 'manual')
    
    # 處理不同模式
    if mode == 'get_latest':
        # 取得最近文章資訊
        latest = builder.get_latest_article()
        if not latest:
            result = {
                'success': False,
                'message': 'no_history',
                'has_articles': False
            }
        else:
            words = builder.extract_words_from_article(latest)
            result = {
                'success': True,
                'has_articles': True,
                'latest_article': str(latest.name),
                'word_count': len(words),
                'words': words[:20]  # 最多顯示 20 個
            }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    elif mode == 'pick_random':
        # 隨機挑選兩個單字
        latest = builder.get_latest_article()
        if not latest:
            result = {'success': False, 'message': 'no_history'}
        else:
            words = builder.extract_words_from_article(latest)
            picked = builder.pick_random_words(words)
            
            if picked:
                result = {
                    'success': True,
                    'word1': picked[0],
                    'word2': picked[1],
                    'from_article': str(latest.name),
                    'available_words': len(words)
                }
            else:
                result = {
                    'success': False,
                    'message': 'all_combinations_used',
                    'available_words': len(words)
                }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    elif mode == 'create':
        # 建立文章和單字
        article_path = builder.create_main_article(
            topic=data['topic'],
            word1=data['word1'],
            word2=data['word2'],
            content=data['article_content'],
            word_list=data['word_list']
        )
        
        created_words = []
        skipped_words = []
        
        for word_data in data['word_details']:
            result = builder.create_word_file(word_data)
            if result:
                created_words.append(word_data['word'])
            else:
                skipped_words.append(word_data['word'])
        
        result = {
            'success': True,
            'article_path': str(article_path),
            'created_words': created_words,
            'skipped_words': skipped_words,
            'total_words': len(data['word_details'])
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
