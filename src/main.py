import feedparser
from google import genai
import os
import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime

# 設定檔案路徑
DB_DIR = "data"
DB_PATH = os.path.join(DB_DIR, "news.json")

# 設定 Gemini API (環境變數)
API_KEY = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY) if API_KEY else None

# 定義抓取的 RSS 來源
FEEDS = {
    "國際新聞": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "科技新聞": "https://techcrunch.com/feed/"
}

def load_db():
    """讀取新聞資料庫"""
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_db(news_list):
    """儲存新聞資料庫"""
    os.makedirs(DB_DIR, exist_ok=True)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(news_list, f, ensure_ascii=False, indent=2)

def fetch_manual_url(url):
    """抓取手動輸入的新聞網址內容"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string if soup.title else "無標題"
        paragraphs = soup.find_all('p')
        content = " ".join([p.get_text() for p in paragraphs[:15]])
        return {
            "category": "手動輸入",
            "title": title,
            "link": url,
            "summary": content[:1500]
        }
    except Exception as e:
        print(f"抓取手動網址時發生錯誤 ({url}): {e}")
        return None

def fetch_news(existing_links):
    """抓取 RSS 中的新聞清單 (過濾已存在的新聞)"""
    all_news = []
    
    manual_url = os.getenv("MANUAL_URL")
    if manual_url and manual_url not in existing_links:
        print(f"偵測到手動網址: {manual_url}")
        manual_news = fetch_manual_url(manual_url)
        if manual_news:
            all_news.append(manual_news)

    for category, url in FEEDS.items():
        print(f"正在抓取 {category} RSS...")
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            if entry.link not in existing_links:
                all_news.append({
                    "category": category,
                    "title": entry.title,
                    "link": entry.link,
                    "summary": entry.summary if hasattr(entry, 'summary') else ""
                })
    return all_news

def process_news_with_gemini(news_list):
    """使用 Gemini 翻譯與摘要新聞"""
    if not client:
        print("未設定 GOOGLE_API_KEY，跳過翻譯步驟。")
        return []

    processed_news = []
    total_news = len(news_list)
    for i, news in enumerate(news_list):
        print(f"[{i+1}/{total_news}] 正在處理: {news['title'][:50]}...")
        prompt = f"""
        你是一位專業的國際新聞與科技新聞編輯。請將以下英文新聞翻譯成繁體中文，並進行深度編輯。

        原文標題：{news['title']}
        原文連結：{news['link']}
        原文內容片段：{news['summary']}
        
        請依照以下格式回傳（請確保內容詳盡且專業）：
        [標題] (請提供一個吸引人的、準確的繁體中文新聞標題)
        [完整摘要] (請根據提供的資訊，撰寫一段 200-400 字的深度摘要，涵蓋新聞背景、主要事件與影響)
        [關鍵重點] (請條列出 3 個這則新聞最值得關注的核心要點)
        """
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            processed_news.append({
                "category": news['category'],
                "original_link": news['link'],
                "content": response.text.strip(),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            print(f"   ✓ 處理完成")
        except Exception as e:
            print(f"   ✗ 處理失敗: {e}")
    return processed_news

def generate_html(all_history):
    """產生具有 Terminal 風格的 Echo Terminal 網頁"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    sorted_news = sorted(all_history, key=lambda x: x.get('timestamp', ''), reverse=True)
    display_news = sorted_news[:20]

    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Echo Terminal | AI-Powered News</title>
        <style>
            :root {{
                --bg-color: #0d1117;
                --card-bg: #161b22;
                --text-main: #c9d1d9;
                --text-muted: #8b949e;
                --accent-color: #2ea043;
                --terminal-green: #3fb950;
                --border-color: #30363d;
            }}
            body {{
                font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', Courier, monospace, 'PingFang TC';
                line-height: 1.7;
                background-color: var(--bg-color);
                color: var(--text-main);
                max-width: 850px;
                margin: 0 auto;
                padding: 40px 20px;
            }}
            header {{
                border-bottom: 2px solid var(--accent-color);
                padding-bottom: 20px;
                margin-bottom: 40px;
            }}
            h1 {{
                font-size: 2.5rem;
                margin: 0;
                color: var(--terminal-green);
                letter-spacing: -1px;
            }}
            .tagline {{
                color: var(--text-muted);
                font-size: 0.9rem;
                margin-top: 5px;
            }}
            .status-bar {{
                font-size: 0.8rem;
                color: var(--accent-color);
                margin-top: 10px;
                background: rgba(46, 160, 67, 0.1);
                padding: 5px 15px;
                border-radius: 4px;
                display: inline-block;
            }}
            .news-card {{
                background: var(--card-bg);
                padding: 30px;
                margin-bottom: 35px;
                border-radius: 8px;
                border: 1px solid var(--border-color);
                transition: transform 0.2s, border-color 0.2s;
            }}
            .news-card:hover {{
                border-color: var(--accent-color);
                transform: translateY(-2px);
            }}
            .category-tag {{
                background: rgba(46, 160, 67, 0.15);
                color: var(--terminal-green);
                padding: 2px 12px;
                border-radius: 12px;
                font-size: 0.75rem;
                font-weight: bold;
                border: 1px solid var(--accent-color);
            }}
            .timestamp {{
                float: right;
                color: var(--text-muted);
                font-size: 0.8rem;
            }}
            .news-content {{
                margin-top: 20px;
                white-space: pre-wrap;
                color: var(--text-main);
                font-size: 1.05rem;
            }}
            a.origin-link {{
                display: inline-block;
                margin-top: 20px;
                color: var(--terminal-green);
                text-decoration: none;
                font-size: 0.9rem;
                border: 1px solid var(--accent-color);
                padding: 5px 15px;
                border-radius: 4px;
            }}
            a.origin-link:hover {{
                background: var(--accent-color);
                color: #fff;
            }}
            footer {{
                text-align: center;
                color: var(--text-muted);
                font-size: 0.8rem;
                margin-top: 80px;
                padding-top: 20px;
                border-top: 1px solid var(--border-color);
            }}
            .cursor {{
                display: inline-block;
                width: 10px;
                height: 1.2em;
                background: var(--terminal-green);
                vertical-align: middle;
                margin-left: 5px;
                animation: blink 1s infinite;
            }}
            @keyframes blink {{
                0% {{ opacity: 1; }} 50% {{ opacity: 0; }} 100% {{ opacity: 1; }}
            }}
        </style>
    </head>
    <body>
        <header>
            <h1>ECHO_TERMINAL<span class="cursor"></span></h1>
            <div class="tagline">Neural News Aggregator & Intelligence Briefing</div>
            <div class="status-bar">STATUS: ONLINE | LAST_FETCH: {now} | DATABASE: {len(all_history)} ENTRIES</div>
        </header>
        
        <main>
    """
    
    for news in display_news:
        html_content += f"""
        <article class="news-card">
            <span class="category-tag">{news['category']}</span>
            <span class="timestamp">SEQ_TS: {news.get('timestamp', '')}</span>
            <div class="news-content">{news['content']}</div>
            <a href="{news['original_link']}" class="origin-link" target="_blank">ACCESS_ORIGINAL_SOURCE ></a>
        </article>
        """
    
    html_content += """
        </main>
        <footer>
            SYSTEM_OUTPUT: Echo Terminal v2.0 // Powered by Gemini 2.5 Intelligence // 2026
        </footer>
    </body>
    </html>
    """
    
    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    print("載入資料庫...")
    db = load_db()
    existing_links = {news['original_link'] for news in db}
    
    print("開始抓取新聞...")
    new_raw_news = fetch_news(existing_links)
    
    if not new_raw_news:
        print("沒有新的新聞需要處理。")
    else:
        print(f"發現 {len(new_raw_news)} 則新新聞，開始由 Gemini 處理...")
        new_processed = process_news_with_gemini(new_raw_news)
        db.extend(new_processed)
        print("儲存資料庫...")
        save_db(db)
    
    print("重新產生網頁檔案...")
    generate_html(db)
    print("完成！")
