#!/bin/bash

# 取得腳本所在的目錄路徑
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "------------------------------------------"
echo "🚀 Starting Gemini News & Morning DJ..."
echo "📅 Date: $(date)"
echo "------------------------------------------"

# 1. 啟動虛擬環境 (如果存在)
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 2. 執行新聞抓取與編輯
echo "📰 Step 1: Fetching and editing news..."
python3 src/main.py

echo "------------------------------------------"
echo "✅ All tasks completed!"
echo "------------------------------------------"
