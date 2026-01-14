---
name: vocabulary-builder
description: C1/C2 高階單字學習文章生成器。支援手動輸入或從歷史文章隨機挑選單字，生成 400-500 字短文和完整單字檔案（Obsidian 格式）
allowed-tools: Bash, Read, Write
---

# Vocabulary Builder Skill

## 重要設定

**Obsidian 輸出路徑**：
```
/Users/jeffliu/Documents/A05_Obsidian Vault/200 VOCABULARY
```

**檔案結構**：
```
A05_Obsidian Vault/
└── Vocabulary/
    ├── Articles/         # 主文檔（日期標題）
    ├── Words/           # 單字檔案
    └── .metadata/       # 追蹤資料（隱藏）
```

**在所有 Python 腳本呼叫中，必須使用以下路徑**：
```json
{
  "output_dir": "/Users/jeffliu/Documents/A05_Obsidian Vault/200 VOCABULARY"
}
```

---

## 功能說明

為英語學習者（C1-C2 程度）生成高品質的單字學習內容，包括：
- ✅ 兩種單字來源：手動輸入 或 從最近文章隨機挑選
- ✅ 智能主題建議：Claude 分析單字後建議主題
- ✅ 生成 400-500 字主題短文（包含 10-15 個高階單字）
- ✅ 自動標記文中所有 C1-C2 單字（Obsidian [[連結]] 格式）
- ✅ 為每個單字生成詳細學習檔案（Form, Meaning, Use）
- ✅ 生成每日單字清單表格
- ✅ 避免重複的單字組合
- ✅ **直接輸出到 Obsidian vault**

---

## 執行步驟

### 步驟 0：確認輸出目錄（每次執行前）

**在執行任何操作前，先確認並建立 Obsidian 輸出目錄**：
```bash
# 定義輸出路徑
OBSIDIAN_VOCAB_DIR="/Users/jeffliu/Documents/A05_Obsidian Vault/200 VOCABULARY"

# 建立必要的資料夾
mkdir -p "$OBSIDIAN_VOCAB_DIR/Articles"
mkdir -p "$OBSIDIAN_VOCAB_DIR/Words"
mkdir -p "$OBSIDIAN_VOCAB_DIR/.metadata"

# 確認建立成功
ls -la "$OBSIDIAN_VOCAB_DIR"
```

**預期輸出**：
```
drwxr-xr-x  Articles/
drwxr-xr-x  Words/
drwxr-xr-x  .metadata/
```

---

### 步驟 1：詢問單字來源

**首先詢問使用者選擇單字來源**：
```
請選擇單字來源：

A) 手動輸入兩個 C1/C2 單字
B) 從最近一次文章中隨機挑選兩個單字

請選擇 A 或 B：
```

---

### 步驟 1.1：如果選擇 A（手動輸入）

**直接詢問兩個單字**：
```
請提供兩個 C1/C2 程度的單字：

1. 單字 1：
2. 單字 2：
```

收到後，**跳到步驟 2**。

---

### 步驟 1.2：如果選擇 B（從歷史挑選）

**先檢查是否有歷史文章**：
```bash
cd ~/.claude/skills/vocabulary-builder/scripts

# 使用 Obsidian 路徑
echo '{
  "mode": "get_latest",
  "output_dir": "/Users/jeffliu/Documents/A05_Obsidian Vault/200 VOCABULARY"
}' | python3 vocabulary_builder.py
```

**處理結果**：

#### 情況 A：有歷史文章
```json
{
  "success": true,
  "has_articles": true,
  "latest_article": "2026-01-14.md",
  "word_count": 12,
  "words": ["eloquent", "articulate", "captivate", ...]
}
```

**告訴使用者**：
```
✅ 找到最近的文章：2026-01-14.md
📚 包含 12 個單字

正在隨機挑選兩個未使用過的單字組合...
```

**執行隨機挑選**：
```bash
echo '{
  "mode": "pick_random",
  "output_dir": "/Users/jeffliu/Documents/A05_Obsidian Vault/200 VOCABULARY"
}' | python3 vocabulary_builder.py
```

**處理挑選結果**：

##### 成功挑選
```json
{
  "success": true,
  "word1": "eloquent",
  "word2": "resilient",
  "from_article": "2026-01-14.md",
  "available_words": 12
}
```

**告訴使用者**：
```
✅ 已挑選單字：
   - 單字 1: eloquent
   - 單字 2: resilient
   
（來自 2026-01-14.md，確保未重複使用過的組合）

繼續進行主題選擇...
```

**跳到步驟 2**。

##### 所有組合都用過
```json
{
  "success": false,
  "message": "all_combinations_used",
  "available_words": 12
}
```

**告訴使用者**：
```
⚠️ 最近文章中的單字組合都已使用過

請改為手動輸入兩個單字：

1. 單字 1：
2. 單字 2：
```

收到後，**跳到步驟 2**。

#### 情況 B：沒有歷史文章
```json
{
  "success": false,
  "message": "no_history",
  "has_articles": false
}
```

**告訴使用者**：
```
ℹ️ 這是您第一次使用，還沒有歷史文章

請手動輸入兩個 C1/C2 單字：

1. 單字 1：
2. 單字 2：
```

收到後，**跳到步驟 2**。

---

### 步驟 2：詢問主題來源

**現在我們已經有兩個單字了**（word1, word2）

詢問主題來源：
```
現在選擇主題方式：

A) 我自己提供主題
B) 請 Claude 建議主題

請選擇 A 或 B：
```

---

### 步驟 2.1：如果選擇 A（手動提供主題）
```
請提供主題（Topic）：
```

收到後，**跳到步驟 3**。

---

### 步驟 2.2：如果選擇 B（Claude 建議主題）

**Claude 分析兩個單字，建議 3-5 個主題**：

#### 分析依據：
1. **語義關聯**：兩個單字的共同主題領域
2. **避免重複**：檢查歷史文章的主題（從 .metadata/word_combinations.json）

**建議主題格式**：
```
基於單字 "{word1}" 和 "{word2}"，我建議以下主題：

1. [主題 1] - [簡短說明]
2. [主題 2] - [簡短說明]
3. [主題 3] - [簡短說明]
4. [主題 4] - [簡短說明]
5. 讓我重新建議其他主題

您選擇哪一個？（輸入數字 1-5）
或者，您可以自己提供主題。
```

**處理使用者回應**：

- 選擇 1-4：使用該主題，**跳到步驟 3**
- 選擇 5：重新分析，生成不同的 3-4 個主題
- 自己輸入主題：使用使用者提供的主題，**跳到步驟 3**

---

### 步驟 3：生成短文內容

現在我們有：
- ✅ word1
- ✅ word2
- ✅ topic

**告訴使用者**：
```
✅ 開始生成學習內容...

📋 設定：
   - 單字 1: {word1}
   - 單字 2: {word2}
   - 主題: {topic}
   - 輸出位置: Obsidian Vault/200 VOCABULARY/

正在生成 400-500 字短文...
```

**生成短文（400-500 字）**：

#### 要求：
1. 第一句或前兩句使用 word1 和 word2
2. 整篇文章包含 10-15 個 C1-C2 單字
3. 緊扣主題
4. 學術但可讀性高
5. 所有 C1-C2 單字用 [[單字]] 標記

---

### 步驟 4：識別並準備單字資料

從生成的短文中：

1. **提取所有 [[單字]]**
2. **統計數量**（應為 10-15 個）
3. **為每個單字準備表格資訊和完整資料**

---

### 步驟 5：呼叫 Python 腳本生成檔案

**重要：必須使用 Obsidian 路徑**
```bash
cd ~/.claude/skills/vocabulary-builder/scripts

cat > /tmp/vocab_input.json << 'EOF'
{
  "mode": "create",
  "output_dir": "/Users/jeffliu/Documents/A05_Obsidian Vault/200 VOCABULARY",
  "word1": "eloquent",
  "word2": "articulate",
  "topic": "Public Speaking",
  "article_content": "[完整 400-500 字短文]",
  "word_list": [...],
  "word_details": [...]
}
EOF

cat /tmp/vocab_input.json | python3 vocabulary_builder.py
```

---

### 步驟 6：回報結果

**回報給使用者**：
```
✅ 學習內容已生成到 Obsidian！

📄 主文檔：
   A05_Obsidian Vault/200 VOCABULARY/Articles/2026-01-14.md
   
📚 新建單字檔案（12 個）：
   ✓ eloquent.md
   ✓ articulate.md
   ✓ captivate.md
   ...
   
💡 在 Obsidian 中查看：
   1. 開啟 Obsidian
   2. 前往 Vocabulary/Articles 資料夾
   3. 點擊今天的日期文章
   4. 所有 [[單字]] 都可以直接點擊查看詳細內容
```

---

## 輸出檔案結構（Obsidian）
```
A05_Obsidian Vault/
└── Vocabulary/
    ├── Articles/
    │   └── 2026-01-14.md          # 主文檔
    ├── Words/
    │   ├── eloquent.md
    │   ├── articulate.md
    │   └── ...
    └── .metadata/
        └── word_combinations.json  # 追蹤資料
```

---

## 注意事項

### Obsidian 整合
- ✅ 檔案直接生成到 vault
- ✅ [[連結]] 格式自動在 Obsidian 中可點擊
- ✅ 可以使用 Obsidian 的所有功能（標籤、反向連結等）
- ⚠️ 如果 Obsidian 正在開啟，新檔案會自動出現

### 路徑設定
- ⚠️ 每次呼叫 Python 腳本都必須包含 `output_dir` 參數
- ⚠️ 路徑必須完全一致：`/Users/jeffliu/Documents/A05_Obsidian Vault/200 VOCABULARY`

