# 🗞️ Gemini News Station (Gemini 個人新聞台)

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Gemini](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-orange?logo=google-gemini)
![GitHub Actions](https://img.shields.io/badge/Automation-GitHub%20Actions-black?logo=github-actions)
![License](https://img.shields.io/badge/License-MIT-green)

這是一個結合 **RSS 抓取**、**Gemini AI 深度編輯** 與 **GitHub Actions 自動化** 的全自動化個人新聞摘要站。它每天會自動為你整理當日重要的國際與科技新聞，並透過 GitHub Pages 免費發布。

---

## ✨ 核心功能

- **🤖 AI 深度編輯**：利用 Google Gemini 2.5-Flash 模型，將英文新聞翻譯為繁體中文，並撰寫 200-400 字的深度摘要與 3 大關鍵點。
- **📅 每日自動更新**：透過 GitHub Actions，每天定時抓取 BBC (國際) 與 TechCrunch (科技) 的最新內容。
- **🔗 手動發布功能**：支援 `workflow_dispatch`。看到喜歡的文章，只需輸入網址，AI 就會幫你編輯並發布到新聞台。
- **🗂️ 歷史紀錄資料庫**：內建 JSON 資料庫，自動跳過已重複處理的新聞，並累積歷史文章。
- **🌐 零成本託管**：完全運行於 GitHub 免費服務，無需租用伺服器。

---

## 🛠️ 技術架構

- **核心語言**: Python 3.12
- **AI 模型**: [Google Gemini API](https://ai.google.dev/) (google-genai)
- **資料抓取**: Feedparser (RSS), BeautifulSoup4 (Web Scraping)
- **自動化**: GitHub Actions (Schedule & Manual)
- **靜態網頁**: GitHub Pages

---

## 🚀 快速開始 (部署指南)

如果你想擁有自己的 Gemini 新聞台：

1. **Fork 本專案**。
2. **取得 Gemini API Key**：前往 [Google AI Studio](https://aistudio.google.com/) 申請免費的金鑰。
3. **設定 GitHub Secrets**：
   - 進入你的 Repo -> **Settings** -> **Secrets and variables** -> **Actions**。
   - 點擊 **New repository secret**。
   - Name: `GOOGLE_API_KEY` / Secret: (填入你的金鑰)。
4. **開啟寫入權限**：
   - 進入 **Settings** -> **Actions** -> **General**。
   - 捲動到 **Workflow permissions**。
   - 選擇 **Read and write permissions** 並點擊 **Save**。
5. **啟用 GitHub Pages**：
   - 進入 **Settings** -> **Pages**。
   - 在 **Branch** 選擇 `main` 並選擇 `/docs` 資料夾，點擊 **Save**。

---

## 📝 如何使用

### 自動模式
系統預設每天 UTC 00:00 (台灣時間 08:00) 自動執行一次，更新首頁新聞。

### 手動發布文章
1. 進入 GitHub Repo 的 **Actions** 頁面。
2. 點擊左側的 **Daily Gemini News Update**。
3. 點擊 **Run workflow**。
4. 在輸入框中貼上你想要翻譯的文章網址。
5. 點擊 **Run workflow**，約 1 分鐘後你的新聞台就會出現新內容！

---

## 📄 開源授權
本專案基於 MIT License 開源。
