# Vocabulary Builder - 使用範例

## 範例 1：手動輸入單字

**對話流程**：
```
使用者：我想使用 vocabulary-builder 學習單字

Claude：請選擇單字來源：
       A) 手動輸入兩個 C1/C2 單字
       B) 從最近一次文章中隨機挑選兩個單字

使用者：A

Claude：請提供兩個 C1/C2 程度的單字：
       1. 單字 1：
       2. 單字 2：

使用者：
       1. eloquent
       2. articulate

Claude：現在選擇主題方式：
       A) 我自己提供主題
       B) 請 Claude 建議主題

使用者：B

Claude：基於單字 "eloquent" 和 "articulate"，我建議以下主題：
       
       1. Public Speaking - 公開演說的技巧與影響力
       2. Effective Communication - 職場溝通與領導力
       3. Persuasion Techniques - 說服與談判的藝術
       4. Language Mastery - 語言表達的精進之道
       5. 讓我重新建議其他主題
       
       您選擇哪一個？

使用者：1

Claude：✅ 開始生成學習內容...
       
       [生成 400-500 字短文]
       [為 12 個單字生成詳細檔案]
       
       ✅ 學習內容生成完成！
       📄 主文檔：2026-01-14.md
       📚 新建 12 個單字檔案
```

---

## 範例 2：從歷史文章隨機挑選

**對話流程**：
```
使用者：使用 vocabulary-builder

Claude：請選擇單字來源：
       A) 手動輸入
       B) 從最近文章隨機挑選

使用者：B

Claude：✅ 找到最近的文章：2026-01-14.md
       📚 包含 12 個單字
       
       正在隨機挑選兩個未使用過的單字組合...
       
       ✅ 已挑選單字：
          - 單字 1: resilient
          - 單字 2: perseverance
       
       現在選擇主題方式：
       A) 我自己提供主題
       B) 請 Claude 建議主題

使用者：B

Claude：[建議 3-5 個主題...]
```

---

## 範例 3：第一次使用（無歷史）
```
使用者：vocabulary-builder

Claude：請選擇單字來源：
       A) 手動輸入
       B) 從最近文章隨機挑選

使用者：B

Claude：ℹ️ 這是您第一次使用，還沒有歷史文章
       
       請手動輸入兩個 C1/C2 單字：
       1. 單字 1：
       2. 單字 2：
```

---

## 測試腳本功能

### 測試 1：檢查歷史文章
```bash
cd ~/.claude/skills/vocabulary-builder/scripts

echo '{"mode": "get_latest"}' | python3 vocabulary_builder.py
```

預期輸出（無歷史）：
```json
{
  "success": false,
  "message": "no_history",
  "has_articles": false
}
```

---

### 測試 2：完整流程測試

建立測試資料：
```bash
# 建立測試文章
mkdir -p ../output/Articles
cat > ../output/Articles/2026-01-14.md << 'TESTEOF'
# 2026-01-14

## 主題：Testing

This is a test article with [[eloquent]] and [[articulate]] words.
Also includes [[resilient]], [[perseverance]], [[captivate]].

## 今日單字清單

| 單字 | 詞性 | 中文意思 | 難度 |
|------|------|---------|------|
| [[eloquent]] | adj. | 雄辯的 | C1 |
| [[articulate]] | v./adj. | 清晰表達 | C1 |
TESTEOF

# 測試讀取
echo '{"mode": "get_latest"}' | python3 vocabulary_builder.py
```

預期輸出：
```json
{
  "success": true,
  "has_articles": true,
  "latest_article": "2026-01-14.md",
  "word_count": 5,
  "words": ["articulate", "captivate", "eloquent", "perseverance", "resilient"]
}
```

---

### 測試 3：隨機挑選
```bash
echo '{"mode": "pick_random"}' | python3 vocabulary_builder.py
```

預期輸出：
```json
{
  "success": true,
  "word1": "eloquent",
  "word2": "resilient",
  "from_article": "2026-01-14.md",
  "available_words": 5
}
```

