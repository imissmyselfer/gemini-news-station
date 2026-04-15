---
title: "【挑戰 1 分鐘】003：讓 Gemini 穿梭 Slack 與 Discord，執行你的自動化密令！"
date: 2026-04-15T00:15:00+08:00
categories: ["挑戰一分鐘"]
tags: ["Gemini", "Automation", "Slack", "Discord", "Workflow"]
author: "Erin"
---

> **「一個人的力量有限，但當 Gemini 同時掌握了 Slack 與 Discord，它就是你的全職幕僚。」**

在前兩篇我們完成了串接，今天我們要來玩真的：讓 Gemini 在不同平台間傳遞訊息，並交辦它三個實戰任務。

---

### ⏱️ 0-20s：啟動雙平台指揮權
確保你的 Gemini CLI 已經同時載入了兩個 MCP。在終端機輸入：
`> /mcp list`
確認 `🟢 slack` 與 `🟢 discord` 都是 Ready 狀態。

### ⏱️ 21-45s：交辦三大自動化任務
現在，你可以直接對 Gemini 下達組合指令，測試它的跨平台處理能力：

#### 任務一：跨平台情報同步
> 「Gemini，請讀取 Discord #dev 頻道的最新進度，並將摘要同步發送到 Slack 的 #project-updates 頻道。」

#### 任務二：自動化週報草稿
> 「Gemini，蒐集今天 Slack 上關於『Bug』的討論，並在 Discord 的 #log 頻道幫我整理成一份待辦清單。」

#### 任務三：全頻道廣播
> 「Gemini，我們要發布 Echo Terminal 的新文章了，請同時在 Slack #general 和 Discord #announcement 發布開張消息！」

### ⏱️ 46-60s：觀察與優化
觀察 Gemini 在切換工具時的思考過程。你會發現它會自動決定先調用 `discord_server` 讀取訊息，再調用 `slack_server` 發送訊息。這就是 **AI Agent** 的真正價值。

---
