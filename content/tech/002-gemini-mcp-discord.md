---
title: "【挑戰 1 分鐘】002：解鎖 Discord 權限，讓 Gemini 成為你的社群管理員！"
date: 2026-04-14T23:55:00+08:00
categories: ["挑戰一分鐘"]
tags: ["Gemini", "MCP", "Discord", "Automation", "Ubuntu"]
author: "Erin"
---

> **「如果說 Slack 是辦公室，Discord 就是你的指揮中心。今天我們要賦予 Gemini 讀取心聲的能力。」**

想讓 Gemini 幫你監控 Discord 頻道，甚至自動回覆訊息？最關鍵的不是代碼，而是開通「讀心術」。

---

### ⏱️ 0-20s：建立機器人與開啟「讀心術」
1. 前往 [Discord Developer Portal](https://discord.com/developers/applications)。
2. **"New Application"** -> 設定名字。
3. 左側選單進入 **"Bot"**：
   - 找到 **"Message Content Intent"** 務必點擊 **開啟 (ON)**！(這是 90% 小白失敗的原因)。
   - 點擊 **"Reset Token"** 取得你的 **Bot Token**。

### ⏱️ 21-40s：一鍵打通任督二脈
回到你的 Ubuntu 終端機，執行以下指令：

```bash
gemini mcp add --scope user discord npx -y @modelcontextprotocol/server-discord --env DISCORD_BOT_TOKEN=你的Token
```

### ⏱️ 41-55s：驗證與邀請
在 Portal 的 "OAuth2" -> "URL Generator"：

勾選 **bot** 和 **applications.commands**。

權限勾選 **Administrator** (懶人包選法)。

複製連結並在瀏覽器打開，將機器人邀請進你的伺服器。

### ⏱️ 56-60s：奇蹟時刻
進入 Gemini CLI 輸入：

「Gemini，幫我看看 Discord 剛才大家在聊什麼？並在 #general 頻道打個招呼！」
