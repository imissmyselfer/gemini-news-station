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
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string if soup.title else "無標題"
        paragraphs = soup.find_all('p')
        content = " ".join([p.get_text() for p in paragraphs[:10]])
        return {
            "category": "手動輸入",
            "title": title,
            "link": url,
            "summary": content[:1000]
        }
    except Exception as e:
        print(f"抓取手動網址時發生錯誤: {e}")
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
        for entry in feed.entries[:5]: # 增加抓取數量
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
    """產生靜態 HTML 檔案 (顯示最近 20 則)"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    # 按時間排序 (最新在前)
    sorted_news = sorted(all_history, key=lambda x: x.get('timestamp', ''), reverse=True)
    display_news = sorted_news[:20] # 顯示最近 20 則

    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Gemini 個人新聞台 (歷史紀錄版)</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f4f4f9; }}
            h1 {{ color: #333; text-align: center; }}
            .date-info {{ text-align: center; color: #666; margin-bottom: 30px; font-size: 0.9em; }}
            .news-card {{ background: #fff; padding: 25px; margin-bottom: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #eee; }}
            .category {{ display: inline-block; background: #00796b; color: #fff; padding: 3px 10px; border-radius: 20px; font-size: 0.75em; margin-bottom: 12px; font-weight: bold; }}
            .timestamp {{ float: right; color: #999; font-size: 0.8em; }}
            .news-content {{ white-space: pre-wrap; color: #444; }}
            a.origin-link {{ display: inline-block; margin-top: 15px; color: #007bff; text-decoration: none; font-weight: 500; }}
            a.origin-link:hover {{ text-decoration: underline; }}
            hr {{ border: 0; border-top: 1px solid #eee; margin: 40px 0; }}
            footer {{ text-align: center; color: #999; font-size: 0.8em; margin-top: 50px; }}
        </style>
    </head>
    <body>
        <h1>Gemini 個人新聞台</h1>
        <p class="date-info">最後更新：{now} (目前共收錄 {len(all_history)} 則新聞)</p>
    """
    
    for news in display_news:
        html_content += f"""
        <div class="news-card">
            <span class="category">{news['category']}</span>
            <span class="timestamp">{news.get('timestamp', '')}</span>
            <div class="news-content">{news['content']}</div>
            <p><a href="{news['original_link']}" class="origin-link" target="_blank">閱讀英文原文 →</a></p>
        </div>
        """
    
    html_content += """
        <footer>Powered by Gemini 2.5 & GitHub Actions</footer>
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
