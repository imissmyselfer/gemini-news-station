---
title: "【挑戰 1 分鐘】實作系列 #004：給 Gemini 一雙「手」。"
date: 2026-04-15T10:00:00+08:00
categories: ["挑戰一分鐘"]
tags: ["Gemini", "MCP", "Filesystem", "Automation", "EchoTerminal", "AI_Automation"]
author: "Erin"
---

> **「讓 AI 不只思考，更能執行。今天，我們為 Gemini CLI 裝上『手』，賦予它與檔案系統互動的能力。」**

在過去的篇章中，我們讓 Gemini 透過 MCP 串接了 Slack 與 Discord，賦予了它溝通的能力。但要成為一個真正強大的 AI 助手，它還需要「雙手」——也就是與檔案系統互動的能力。今天，我們將深入探討如何達成這點，並解決過程中可能遇到的「斷鏈」問題。

---

### ⏱️ 0-15s：建立 AI 的行為準則：`.gemini_rules` 的必要性

當 AI 開始能夠存取或修改檔案時，一個清晰的行為準則就變得至關重要。`.gemini_rules` 文件就像是 AI 的「契約」，它定義了：

*   **何時可以存取檔案：** 哪些操作是允許的？
*   **存取的範圍：** 哪些目錄是安全的（Trust Folders）？
*   **操作的規範：** 數據格式、路徑處理、安全性考量等。

沒有 `.gemini_rules`，AI 就像一個沒有方向的工具，容易誤操作或產生安全風險。它確保了 AI 的行動是可控、安全且符合預期的。

### ⏱️ 16-35s：Trust Folder vs. MCP：權限的疆界

在檔案系統整合的早期，我們可能會遇到「Trust Folder」的概念。這是一種將 AI 的存取權限限制在特定目錄範圍內的方法。雖然簡單直接，但往往過於嚴苛，難以應對複雜的專案結構。

MCP (Model Context Protocol) 則提供了一個更為現代且彈性的解決方案。它不單純是限制目錄，而是建立了一種「溝通協定」，讓 AI 能夠透過標準化的方式與不同的服務（包括檔案系統）互動。MCP 的核心在於「語境」與「協定」，讓 AI 能夠理解並操作，而不僅僅是被動地存取預設的資料夾。

### ⏱️ 36-55s：『合併路徑』的智慧：MCP 檔案系統整合實錄

過去，當我們需要讓 Gemini 存取不同專案或不同層級的檔案時，可能會面臨「Disconnected」的問題—— AI 無法統一地看見或操作所有它需要的資源。

MCP 透過其「檔案系統 MCP」模組，實踐了「合併路徑」(Merged Path) 的解決方案。這意味著：

*   **統一視角：** MCP 能夠整合來自不同來源（例如，系統內的多個專案目錄）的檔案路徑，為 Gemini 提供一個統一的、可操作的視圖。
*   **智慧路由：** 當 Gemini 請求存取某個檔案時，MCP 會智慧地路由這個請求到正確的位置，無論該檔案位於專案的 `src` 目錄，還是獨立的 `data` 目夾。
*   **跨目錄操作：** 透過這種方式，Gemini 可以跨越專案的界限，讀取、寫入或修改任何它被授權存取的檔案，解決了傳統 Trust Folder 的限制。

在我們的案例中，這意味著 Gemini CLI 可以安全地在 `/[YOUR_PATH]/gemini/ai-music-curator/data/` 或 `/[YOUR_PATH]/gemini/gemini-news-station/content/tech/` 等多個位置進行檔案操作。

### ⏱️ 56-60s：賦予 Gemini 你的「智慧之手」

現在，你可以在 Gemini CLI 中測試它與檔案系統的互動了。嘗試以下指令：

「Gemini，請在 `/[YOUR_PATH]/gemini/gemini-news-station/content/tech/` 目錄下，列出所有 markdown 檔案。」

或者更進一步：

「Gemini，請將 `/[YOUR_PATH]/gemini/ai-music-curator/data/liked_songs.json` 的內容讀取出來。」

你會看到 Gemini 透過 MCP 提供的能力，順暢地執行這些檔案操作，就像它擁有了一雙聽從你指令的「智慧之手」。

---
