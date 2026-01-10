# 我的 Claude Skills 集合

這是我個人的 Claude Code Skills 專案，包含多個實用的工作流程自動化 Skills。

## 📚 Skills 列表

### 1. file-organizer
**功能**：整理雜亂的資料夾，依檔案類型自動分類

**特色**：
- 支援多種檔案類型（文件、圖片、影片、壓縮檔等）
- 只整理根目錄檔案，保留子資料夾
- 移動前會先確認

**使用**：說「整理我的下載資料夾」

---

### 2. doc-summarizer
**功能**：文件摘要器，提供三層次摘要

**特色**：
- 一句話摘要（30字）
- 重點摘要（3-5個要點）
- 詳細摘要（分段說明）
- 支援 .txt, .md, .pdf

**使用**：上傳文件並說「請摘要這份文件」

---

### 3. daily-report
**功能**：全球市場日報生成器

**特色**：
- 涵蓋 10 個區域（北美、南美、中國、歐洲、日本、韓國、台灣、中東、東南亞、印度）
- 多語言搜尋（用當地語言搜尋當地新聞）
- 深度分析（每區域約 700 字整合報告）
- 嚴格日期驗證
- 每區域至少 10 則新聞

**使用**：說「daily report」然後輸入日期和主題

---

## 🚀 安裝方式

### 安裝所有 Skills
```bash
# 複製所有 Skills 到 Claude 資料夾
cp -r */ ~/.claude/skills/
```

### 安裝單一 Skill
```bash
# 只安裝檔案整理器
cp -r file-organizer ~/.claude/skills/

# 只安裝文件摘要器
cp -r doc-summarizer ~/.claude/skills/

# 只安裝日報生成器
cp -r daily-report ~/.claude/skills/
```

---

## 📖 使用說明

1. 確保已安裝 Claude Code
2. 複製 Skills 到 `~/.claude/skills/`
3. 啟動 Claude Code：`claude`
4. Skills 會自動載入

### 驗證安裝

在 Claude Code 中執行：
```
What Skills are available?
```

---

## 🛠️ 專案結構
```
my-claude-skills/
├── README.md
├── .gitignore
├── file-organizer/
│   └── SKILL.md
├── doc-summarizer/
│   ├── SKILL.md
│   └── examples/
│       └── sample-output.md
└── daily-report/
    └── SKILL.md
```

---

**建立日期**：2025-01-11  
**最後更新**：2025-01-11  
**作者**：Jeff Liu
