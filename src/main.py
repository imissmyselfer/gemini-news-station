import feedparser
import google.generativeai as genai
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 設定 Gemini API (環境變數)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

# 定義抓取的 RSS 來源
FEEDS = {
    "國際新聞": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "科技新聞": "https://techcrunch.com/feed/"
}

def fetch_manual_url(url):
    """抓取手動輸入的新聞網址內容"""
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        # 簡單抓取標題和所有段落內容
        title = soup.title.string if soup.title else "無標題"
        paragraphs = soup.find_all('p')
        content = " ".join([p.get_text() for p in paragraphs[:10]]) # 取前 10 段以避免太長
        return {
            "category": "手動輸入",
            "title": title,
            "link": url,
            "summary": content[:1000] # 限制長度
        }
    except Exception as e:
        print(f"抓取手動網址時發生錯誤: {e}")
        return None

def fetch_news():
    """抓取 RSS 中的新聞清單"""
    all_news = []
    
    # 檢查是否有手動網址
    manual_url = os.getenv("MANUAL_URL")
    if manual_url:
        print(f"偵測到手動網址: {manual_url}")
        manual_news = fetch_manual_url(manual_url)
        if manual_news:
            all_news.append(manual_news)

    for category, url in FEEDS.items():
        print(f"正在抓取 {category} RSS...")
        feed = feedparser.parse(url)
        # 每個分類取前 3 則新聞
        for entry in feed.entries[:3]:
            all_news.append({
                "category": category,
                "title": entry.title,
                "link": entry.link,
                "summary": entry.summary if hasattr(entry, 'summary') else ""
            })
    return all_news

def process_news_with_gemini(news_list):
    """使用 Gemini 翻譯與摘要新聞"""
    if not GOOGLE_API_KEY:
        print("未設定 GOOGLE_API_KEY，跳過翻譯步驟。")
        return news_list

    model = genai.GenerativeModel("gemini-2.0-flash")
    
    processed_news = []
    for news in news_list:
        prompt = f"""
        請將以下英文新聞翻譯成中文並寫一段簡短摘要。
        標題：{news['title']}
        連結：{news['link']}
        內容摘要：{news['summary']}
        
        請以以下格式回傳：
        [標題] (翻譯後的中文標題)
        [摘要] (翻譯後的中文摘要，約 50-100 字)
        """
        try:
            response = model.generate_content(prompt)
            # 解析回應內容 (這裡簡化處理)
            processed_news.append({
                "category": news['category'],
                "original_link": news['link'],
                "content": response.text.strip()
            })
        except Exception as e:
            print(f"處理新聞時發生錯誤: {e}")
            processed_news.append({
                "category": news['category'],
                "original_link": news['link'],
                "content": f"[標題] {news['title']} (翻譯失敗)\n[摘要] 無法翻譯。"
            })
    return processed_news

def generate_html(processed_news):
    """產生靜態 HTML 檔案"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Gemini 個人新聞台</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f4f4f9; }}
            h1 {{ color: #333; text-align: center; }}
            .date {{ text-align: center; color: #666; margin-bottom: 30px; }}
            .news-card {{ background: #fff; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .category {{ display: inline-block; background: #e0f2f1; color: #00796b; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; margin-bottom: 10px; }}
            .news-content {{ white-space: pre-wrap; }}
            a {{ color: #007bff; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <h1>Gemini 個人新聞台</h1>
        <p class="date">更新時間：{now}</p>
    """
    
    for news in processed_news:
        html_content += f"""
        <div class="news-card">
            <span class="category">{news['category']}</span>
            <div class="news-content">{news['content']}</div>
            <p><a href="{news['original_link']}" target="_blank">查看原文</a></p>
        </div>
        """
    
    html_content += """
    </body>
    </html>
    """
    
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    print("開始抓取新聞...")
    raw_news = fetch_news()
    print(f"共抓取 {len(raw_news)} 則新聞，開始由 Gemini 處理...")
    processed = process_news_with_gemini(raw_news)
    print("產生網頁檔案...")
    generate_html(processed)
    print("完成！")
