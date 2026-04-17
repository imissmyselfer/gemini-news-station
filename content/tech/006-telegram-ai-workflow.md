---
title: 【挑戰 1 分鐘】006：Telegram + Claude Web + Claude Code：AI 工具協作完全指南
date: 2026-04-17T00:30:00+08:00
categories:
  - 挑戰一分鐘
tags:
  - Telegram
  - Automation
technologies:
  - Telegram Bot
  - Claude Web Interface
  - Claude Code CLI
  - python-telegram-bot
  - Gemini CLI
  - Prompt Engineering
author: Erin
---

> **「從想法到成品，只需數分鐘。今天，我們將展示三個 AI 工具如何完美協作，用自然語言描述需求，自動生成一個完整的 Telegram AI Bot 專案。」**
>
> 你有沒有想過，讓 AI 幫你直接生成一整個專案？不是簡單的代碼片段，而是包括項目結構、依賴配置、核心邏輯、文檔的完整系統——今天，我們就來展示這個奇蹟。

---

### ⏱️ 0-15s：準備舞台：安裝 Telegram 到 Gemini CLI

首先，讓我們為 Gemini CLI 裝上「Telegram 手臂」，使它能與 Telegram 平台互動。這需要用 MCP（Model Context Protocol）集成。

**前置條件：**
*   ✅ Gemini CLI 已安裝
*   ✅ 一個有效的 Telegram Bot Token（從 @BotFather 取得）

**設定步驟：**

**1️⃣ 取得 Telegram Chat ID**
```bash
# 用 Telegram API 驗證你的 Bot Token，並取得基本資訊
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe
```

**2️⃣ 編輯 `.gemini/settings.json`，添加 Telegram MCP 伺服器**
```json
{
  "mcpServers": {
    "telegram": {
      "command": "npx",
      "args": ["-y", "@iqai/mcp-telegram"],
      "env": {
        "TELEGRAM_BOT_TOKEN": "$TELEGRAM_BOT_TOKEN_GEMINI",
        "TELEGRAM_CHAT_ID": "$TELEGRAM_CHAT_ID_GEMINI"
      }
    }
  }
}
```
---

### ⏱️ 16-40s：AI 的想法工廠：在 Claude Web 中生成完整 Prompt

現在來到最關鍵的一步——用自然語言告訴 Claude Web「你想要什麼樣的項目」。Claude Web 會生成一個**完整的 Prompt 檔案**（約 130 行），可直接用於 Claude Code。

**在 Claude Web 上，發送這樣的需求：**

```
我需要一個完整的 Telegram AI Chatbot 專案。

需求：
1. 使用 Python 3.11+，框架用 python-telegram-bot
2. 支援 Gemini 和 Claude 兩個 AI 模型，無縫切換
3. 每個使用者有獨立的對話歷史（最多 20 輪對話）
4. 實現 /start, /help, /model, /clear 等指令
5. 使用 async/await 非同步架構
6. 完整的錯誤處理和日誌系統

請生成一份詳細的實現 Prompt，包括專案結構、所有模組代碼、設定檔案和文檔。
```

**Claude Web 將為你生成：**
- ✅ **一個完整的 Prompt 檔案**（如 `telegram-ai-bot-prompt.md`，約 130 行）
- ✅ 專案結構和所有檔案清單
- ✅ 每個模組的完整代碼
- ✅ 環境設定和依賴配置
- ✅ 詳細的使用文檔範本

**下一步：** 直接複製整個 Prompt 檔案，貼到 Claude Code 中執行！

---

### ⏱️ 41-55s：實戰執行：在 Claude Code 中一鍵生成項目

現在拿著 Claude Web 生成的 **telegram-ai-bot-prompt.md**（130 行的完整 Prompt），直接貼到 Claude Code 中執行。

**在 Claude Code 中的工作流程：**

```bash
# 1. 啟動 Claude Code
claude

# 2. 在 Claude Code 中新建聊天窗口
# 複製 Claude Web 生成的 telegram-ai-bot-prompt.md 內容
# 完整貼上到 Claude Code 的聊天框中
# ✨ Claude Code 會自動處理一切：
#    - 建立專案資料夾
#    - 初始化 Git
#    - 建立所有檔案
```

**貼上後，Claude Code 會自動：**
- 🚀 建立所有 Python 模組（main.py, bot.py, ai_client.py 等）
- ✅ 生成 pyproject.toml 和 .env.example
- 📦 建立虛擬環境（venv）並安裝依賴
- 💾 初始化 Git 並自動提交
- 🔍 驗證所有代碼無語法錯誤
- 📝 生成完整文檔（README.md, SETUP.md, QUICKSTART.md）

**這就是 Claude Code 的超能力：** 一次性處理複雜的多檔案項目。

---

### ⏱️ 56-60s：閉環驗證：Gemini CLI 測試 Telegram Bot

項目生成完成後，用 Gemini CLI 幫你驗證 Bot 是否運作：

```bash
# 在 Claude Code 終端執行
python -m src.main

# 同時開另一個終端，用 Gemini CLI 測試
gemini --ask "用 Telegram Bot API 測試這個 Bot 是否在線。Token: $TELEGRAM_BOT_TOKEN"
```

**完整工作流程驗證清單：**
- ✅ Bot 正確啟動（日誌顯示「✅ Bot 已啟動」）
- ✅ Gemini 客戶端已初始化
- ✅ Claude 客戶端已初始化
- ✅ 在 Telegram 中發送訊息，Bot 正確回覆
- ✅ `/model claude` 指令工作正常
- ✅ 對話歷史正確保留

---

### 🎯 三個 AI 工具的完美協作

| 工具 | 角色 | 貢獻 |
|------|------|------|
| **Claude Web** | 💭 思想家 | 將你的需求轉化為詳細的技術規格 |
| **Claude Code** | 🔨 工匠 | 生成完整代碼、管理檔案結構、自動化工作流 |
| **Gemini CLI** | 🔍 測試官 | 驗證成果、執行動態測試、監控運行狀態 |

---

### 🚀 接下來可以嘗試

- 💬 **多模型支援：** 用同樣的流程，新增更多 AI 模型（OpenAI、Anthropic 等）
- 🌐 **跨平台擴展：** Discord Bot、Slack Bot、微信機器人——用同樣的思路生成
- 📊 **增強型智能：** 新增數據庫、Redis 快取、訊息持久化
- 🤖 **自動化工作流程：** 讓 Claude Code 自動執行測試、部署、監控
- 🎯 **學習這個模式：** 任何複雜的項目都可以用「Claude Web（設計）→ Claude Code（實現）→ Gemini CLI（驗證）」的三步法

---

### 📌 核心洞察

**AI 不再只是回答問題的工具，而是可以一起協作完成真實工程的夥伴。**

當你用自然語言描述需求時，不同的 AI 工具各司其職：
- 一個幫你「想清楚」
- 一個幫你「做出來」
- 一個幫你「驗證對」

這就是未來的開發方式。🎉

---

