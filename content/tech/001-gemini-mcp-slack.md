---
title: "【挑戰 1 分鐘】001：讓 Gemini CLI 接上 Slack，打造你的 AI 通訊官！"
date: 2026-04-14T23:30:00+08:00
categories: ["挑戰一分鐘"]
tags: ["Gemini", "MCP", "Slack", "Automation", "Ubuntu"]
author: "Erin"
---

> **「從 0 到 🟢，只需 60 秒。這不只是一個新聞台，這是一個不斷進化的 AI 實驗室。」**

想讓你的 Gemini 不只會聊天，還能幫你在 Slack 發報、讀訊息？不需要寫長長的代碼，我們用 **MCP (Model Context Protocol)** 瞬間打通！

---

### ⏱️ 0-15s：取得靈魂鑰匙 (Slack Token)
1. 進入 [Slack API 官網](https://api.slack.com/apps)。
2. 點擊 **"Create New App"** -> **"From Scratch"**。
3. 在 **"OAuth & Permissions"** 勾選 `chat:write` 與 `channels:read` 權限。
4. 點擊 **"Install to Workspace"**，複製那串以 `xoxb-` 開頭的 **Bot User OAuth Token**。

### ⏱️ 16-40s：一鍵注入超能力
在你的 Ubuntu 終端機，執行以下指令（替換你的 Token）：

```bash
gemini mcp add --scope user slack npx -y @modelcontextprotocol/server-slack --env SLACK_BOT_TOKEN=你的Token
```

### ⏱️ 41-55s：驗證綠燈
進入 Gemini CLI 後輸入：

```bash
> /mcp list
```
看見 `🟢 slack - Ready` 了嗎？通訊權限已解鎖！

### ⏱️ 56-60s：奇蹟時刻
對著 Gemini 下令：

「請幫我在 Slack 的 #general 頻道發送一則訊息：『Ubuntu 24.04 報告！Gemini 已成功接管通訊通道。🚀』」
