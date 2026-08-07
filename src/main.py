import feedparser
from google import genai
import os
import requests
import json
import html
import re
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlparse, urlunparse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# 設定檔案路徑
DB_DIR = "data"
DB_PATH = os.path.join(DB_DIR, "news.json")
DOCS_DIR = "docs"

# 設定 Gemini API (環境變數)
API_KEY = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY) if API_KEY else None

# 定義抓取的 RSS 來源
FEEDS = {
    "國際新聞": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "科技新聞": "https://techcrunch.com/feed/",
    "Mountain View 當地新聞": "https://www.mv-voice.com/feed/",
    "Palo Alto 當地新聞": "https://www.paloaltoonline.com/feed/"
}

def clean_url(url):
    """移除網址中的追蹤參數以進行準確去重"""
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))

def dedup_keys(link, title):
    """產生一則新聞的去重鍵，涵蓋網址、跨站同步轉載與標題三種重複情況"""
    keys = {f"url:{clean_url(link)}"}

    # 姊妹報（如 MV Voice / Palo Alto Online）會同步轉載同一篇稿子，
    # 網址 path 完全相同、只有 host 不同，因此單獨用 path 當去重鍵。
    path = urlparse(link).path.rstrip('/')
    if len(path) >= 25:
        keys.add(f"path:{path}")

    # 標題正規化：去除大小寫、空白與標點差異 (\w 在 Python 3 已涵蓋中日韓文字)
    normalized = re.sub(r'\W', '', (title or '').lower())[:40]
    if len(normalized) >= 10:
        keys.add(f"title:{normalized}")

    return keys

def is_duplicate(news, seen):
    """判斷新聞是否重複；若不重複則把它的去重鍵記入 seen"""
    keys = dedup_keys(news['link'], news['title'])
    if keys & seen:
        return True
    seen |= keys
    return False

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

def fetch_tldr():
    """抓取 TLDR Newsletter 的最新內容"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    all_articles = []
    try:
        response = requests.get("https://tldr.tech", headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        articles = soup.find_all('article')
        for article in articles[:3]:
            try:
                title_elem = article.find('h2') or article.find('h3')
                link_elem = article.find('a')

                if not title_elem or not link_elem:
                    continue

                title = title_elem.get_text(strip=True)
                link = link_elem.get('href', '')

                if not link.startswith('http'):
                    link = 'https://tldr.tech' + link if link.startswith('/') else ''

                if link and title:
                    content = article.get_text(separator=' ', strip=True)[:1500]
                    all_articles.append({
                        "category": "TLDR Newsletter",
                        "title": title,
                        "link": link,
                        "summary": content
                    })
            except Exception as e:
                print(f"   TLDR 單篇解析失敗: {e}")
                continue
    except Exception as e:
        print(f"抓取 TLDR 時發生錯誤: {e}")
    return all_articles

def fetch_1440():
    """抓取 1440 Daily Digest 的最新內容"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    all_articles = []
    try:
        response = requests.get("https://join1440.com", headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        articles = soup.find_all('article')
        for article in articles[:3]:
            try:
                title_elem = article.find('h2') or article.find('h3')
                link_elem = article.find('a')

                if not title_elem or not link_elem:
                    continue

                title = title_elem.get_text(strip=True)
                link = link_elem.get('href', '')

                if not link.startswith('http'):
                    link = 'https://join1440.com' + link if link.startswith('/') else ''

                if link and title:
                    content = article.get_text(separator=' ', strip=True)[:1500]
                    all_articles.append({
                        "category": "1440 Daily Digest",
                        "title": title,
                        "link": link,
                        "summary": content
                    })
            except Exception as e:
                print(f"   1440 單篇解析失敗: {e}")
                continue
    except Exception as e:
        print(f"抓取 1440 時發生錯誤: {e}")
    return all_articles

def fetch_rundown():
    """抓取 The Rundown AI 的最新內容"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    all_articles = []
    try:
        response = requests.get("https://therundown.ai", headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        articles = soup.find_all('article')
        for article in articles[:3]:
            try:
                title_elem = article.find('h2') or article.find('h3')
                link_elem = article.find('a')

                if not title_elem or not link_elem:
                    continue

                title = title_elem.get_text(strip=True)
                link = link_elem.get('href', '')

                if not link.startswith('http'):
                    link = 'https://therundown.ai' + link if link.startswith('/') else ''

                if link and title:
                    content = article.get_text(separator=' ', strip=True)[:1500]
                    all_articles.append({
                        "category": "The Rundown AI",
                        "title": title,
                        "link": link,
                        "summary": content
                    })
            except Exception as e:
                print(f"   The Rundown AI 單篇解析失敗: {e}")
                continue
    except Exception as e:
        print(f"抓取 The Rundown AI 時發生錯誤: {e}")
    return all_articles

def fetch_los_altos():
    """抓取 Los Altos Online 的最新內容"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    all_articles = []
    try:
        response = requests.get("https://www.losaltosonline.com/news/", headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        articles = soup.find_all('article', limit=5)
        for article in articles:
            try:
                title_elem = article.find(class_='tnt-headline')
                link_elem = article.find('a')

                if not title_elem or not link_elem:
                    continue

                title = title_elem.get_text(strip=True)
                link = link_elem.get('href', '')

                if not link.startswith('http'):
                    link = 'https://www.losaltosonline.com' + link if link.startswith('/') else ''

                if link and title:
                    content = article.get_text(separator=' ', strip=True)[:1500]
                    all_articles.append({
                        "category": "Los Altos 當地新聞",
                        "title": title,
                        "link": link,
                        "summary": content
                    })
            except Exception as e:
                print(f"   Los Altos 單篇解析失敗: {e}")
                continue
    except Exception as e:
        print(f"抓取 Los Altos 時發生錯誤: {e}")
    return all_articles

def fetch_news(seen):
    """抓取各來源新聞清單 (過濾已存在與本次重複的新聞)

    seen 會隨著收錄逐則更新，因此同一次執行中重複出現的新聞
    （例如姊妹報同步轉載的同一篇稿子）也會被擋下來。
    """
    all_news = []

    def collect(candidates, limit=5):
        for news in candidates[:limit]:
            if is_duplicate(news, seen):
                print(f"   跳過重複新聞: {news['title'][:30]}...")
            else:
                all_news.append(news)

    manual_url = os.getenv("MANUAL_URL")
    if manual_url:
        print(f"偵測到手動網址: {manual_url}")
        manual_news = fetch_manual_url(manual_url)
        if manual_news:
            collect([manual_news])

    for category, url in FEEDS.items():
        print(f"正在抓取 {category} RSS...")
        feed = feedparser.parse(url)
        # 限制每類新聞抓取數量：每個 RSS 來源最多 5 則
        collect([{
            "category": category,
            "title": entry.title,
            "link": entry.link,
            "summary": entry.summary if hasattr(entry, 'summary') else ""
        } for entry in feed.entries[:5]])

    # 抓取電子報與網頁爬蟲來源
    for label, fetcher in [
        ("TLDR Newsletter", fetch_tldr),
        ("1440 Daily Digest", fetch_1440),
        ("The Rundown AI", fetch_rundown),
        ("Los Altos 當地新聞", fetch_los_altos),
    ]:
        print(f"正在抓取 {label}...")
        collect(fetcher())

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
	注意：請直接開始輸出內容，**絕對不要**包含任何開場白、禮貌性回應（例如「好的」、「沒問題」）或自我介紹（例如「身為一位編輯...」）。
        """
        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt
            )
            processed_news.append({
                "category": news['category'],
                "original_link": news['link'],
                "content": response.text.strip(),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "original_title": news['title']
            })
            print(f"   ✓ 處理完成")
        except Exception as e:
            print(f"   ✗ 處理失敗: {e}")
    return processed_news

# Swiss 極簡版型樣式 (非 f-string，避免大括號轉義)
PAGE_STYLE = """
    * { box-sizing: border-box; }
    :root {
        --ink: #000;
        --muted: #999;
        --line: #000;
        --accent: #0033cc;
    }
    body {
        margin: 0;
        background: #fff;
        color: var(--ink);
        font-family: 'Helvetica Neue', Inter, 'PingFang TC', 'Noto Sans TC', system-ui, sans-serif;
        max-width: 820px;
        margin: 0 auto;
        padding: 60px 24px 120px;
        line-height: 1.75;
    }
    header {
        border-bottom: 3px solid var(--line);
        padding-bottom: 18px;
    }
    h1 {
        font-size: 3.2rem;
        font-weight: 800;
        letter-spacing: -0.045em;
        margin: 0;
        line-height: 1;
    }
    .tagline {
        color: var(--muted);
        font-size: 0.8rem;
        margin-top: 10px;
        text-transform: uppercase;
        letter-spacing: 0.12em;
    }
    .meta {
        font-size: 0.72rem;
        color: var(--muted);
        margin-top: 12px;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    article {
        display: grid;
        grid-template-columns: 52px 1fr;
        gap: 28px;
        padding: 38px 0;
        border-bottom: 1px solid #ddd;
    }
    .num {
        font-size: 0.8rem;
        font-weight: 700;
        color: var(--muted);
        padding-top: 5px;
    }
    .cat {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--accent);
    }
    .time {
        float: right;
        font-size: 0.7rem;
        color: var(--muted);
        letter-spacing: 0.06em;
    }
    h2 {
        font-size: 1.5rem;
        font-weight: 700;
        line-height: 1.35;
        margin: 12px 0 16px;
        letter-spacing: -0.02em;
    }
    .summary {
        font-size: 0.92rem;
        color: #333;
        white-space: pre-wrap;
    }
    .points {
        margin: 22px 0 0;
        padding: 16px 0 0;
        list-style: none;
        border-top: 1px solid #ddd;
    }
    .points li {
        font-size: 0.85rem;
        color: #555;
        margin-bottom: 8px;
        padding-left: 18px;
        position: relative;
    }
    .points li:before {
        content: "+";
        position: absolute;
        left: 0;
        color: var(--accent);
    }
    .src {
        display: inline-block;
        margin-top: 22px;
        font-size: 0.78rem;
        font-weight: 700;
        color: var(--accent);
        text-decoration: none;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .src:hover { text-decoration: underline; }
    footer {
        margin-top: 80px;
        padding-top: 20px;
        border-top: 3px solid var(--line);
        font-size: 0.72rem;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.12em;
    }
    @media (max-width: 600px) {
        h1 { font-size: 2.2rem; }
        article { grid-template-columns: 1fr; gap: 0; }
        .num { display: none; }
    }
"""

def parse_gemini_content(content):
    """將 Gemini 回傳的 [標題]/[完整摘要]/[關鍵重點] 拆成結構化欄位"""
    title, summary, points = "", "", []

    match = re.search(r"\[標題\]\s*(.+)", content)
    if match:
        title = match.group(1).strip()

    match = re.search(r"\[(?:完整摘要|深度摘要)\]\s*(.*?)(?=\n\s*\[|$)", content, re.S)
    if match:
        summary = match.group(1).strip()

    match = re.search(r"\[關鍵重點\]\s*(.*)$", content, re.S)
    if match:
        for line in match.group(1).strip().split("\n"):
            line = re.sub(r"^\d+[\.、)]\s*", "", line.strip())
            line = re.sub(r"^[-*•]\s*", "", line)
            if line:
                points.append(line)

    if not title:
        title = content.split("\n")[0].strip()[:80]
    if not summary:
        summary = content
    return title, summary, points[:3]

def format_inline(text):
    """先 HTML escape，再把 **粗體** 還原成 <strong> 標籤"""
    escaped = html.escape(text)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)

def generate_html(all_history):
    """產生 Swiss 極簡風格的 Echo Terminal 網頁"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    sorted_news = sorted(all_history, key=lambda x: x.get('timestamp', ''), reverse=True)
    
    unique_news = []
    seen_titles = set()
    for news in sorted_news:
        content_title = ""
        if "[標題]" in news['content']:
            content_title = news['content'].split("[標題]")[1].strip()[:15]
        
        if content_title not in seen_titles:
            unique_news.append(news)
            seen_titles.add(content_title)
            
    display_news = unique_news[:20]

    html_content = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Echo Terminal | Intelligence Briefing</title>
    <style>{PAGE_STYLE}</style>
</head>
<body>
    <header>
        <h1>ECHO TERMINAL</h1>
        <div class="tagline">Neural Information System — Intelligence Briefing</div>
        <div class="meta">共 {len(all_history)} 則紀錄 · 最後同步 {now}</div>
    </header>
    <main>
"""

    for i, news in enumerate(display_news, 1):
        title, summary, points = parse_gemini_content(news['content'])
        points_html = ""
        if points:
            items = "".join(f"<li>{format_inline(p)}</li>" for p in points)
            points_html = f'<ul class="points">{items}</ul>'

        html_content += f"""
        <article>
            <div class="num">{i:02d}</div>
            <div>
                <span class="cat">{html.escape(news['category'])}</span>
                <span class="time">{html.escape(news.get('timestamp', ''))}</span>
                <h2>{format_inline(title)}</h2>
                <div class="summary">{format_inline(summary)}</div>
                {points_html}
                <a class="src" href="{html.escape(news['original_link'])}" target="_blank">閱讀原文 →</a>
            </div>
        </article>
"""

    html_content += """
    </main>
    <footer>
        ECHO TERMINAL v3.0 · Swiss Minimal Interface · 2026
    </footer>
</body>
</html>
"""
    
    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

def send_daily_email(processed_news_list):
    """發送每日新聞摘要 Email"""
    gmail_user = os.getenv("GMAIL_USER")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")
    recipient = os.getenv("RECIPIENT_EMAIL")

    if not (gmail_user and gmail_password and recipient):
        print("Email 配置不完整，跳過寄送。請檢查 GMAIL_USER, GMAIL_APP_PASSWORD, RECIPIENT_EMAIL 環境變數。")
        return

    if not processed_news_list:
        print("今天沒有新聞要寄送。")
        return

    try:
        # 提取每則新聞的標題和關鍵重點
        email_articles = []
        for news in processed_news_list:
            content = news.get('content', '')

            # 從 Gemini 回傳的格式解析標題和重點
            # 格式 1: [標題] xxx\n...
            # 格式 2: 標題內容\n[深度摘要] 或 [完整摘要]...
            # 格式 3: [標題內容]\n[摘要]...
            title = ""
            if "[標題]" in content:
                title = content.split("[標題]")[1].split("\n")[0].strip()
            else:
                # 嘗試取第一行作為標題
                first_line = content.split("\n")[0].strip()
                if first_line:
                    # 去除方括號、**、等格式符號
                    title = first_line.replace("[", "").replace("]", "").replace("**", "").strip()

            key_points = ""
            if "[關鍵重點]" in content:
                key_points_section = content.split("[關鍵重點]")[1].strip()
                # 只取前 300 字
                key_points = key_points_section[:300]
            elif "[深度摘要]" in content or "[完整摘要]" in content:
                # 如果沒有關鍵重點，嘗試從摘要提取
                if "[深度摘要]" in content:
                    summary = content.split("[深度摘要]")[1].strip()
                else:
                    summary = content.split("[完整摘要]")[1].strip()
                # 取前 300 字作為關鍵重點
                key_points = summary[:300]

            if title:
                email_articles.append({
                    "title": title,
                    "key_points": key_points,
                    "link": news.get('original_link', ''),
                    "category": news.get('category', '')
                })

        if not email_articles:
            print("沒有可寄送的新聞內容。")
            return

        # 產生 HTML 格式的 Email 內容
        now = datetime.now().strftime("%Y-%m-%d")
        email_html = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'PingFang TC', 'Microsoft YaHei', Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ border-bottom: 2px solid #2aa198; padding-bottom: 15px; margin-bottom: 25px; }}
                .header h1 {{ margin: 0; color: #2aa198; font-size: 24px; }}
                .header p {{ margin: 5px 0 0 0; color: #666; font-size: 14px; }}
                .news-item {{ margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid #eee; }}
                .news-item:last-child {{ border-bottom: none; }}
                .news-category {{ display: inline-block; background: #2aa198; color: white; padding: 3px 10px; border-radius: 3px; font-size: 12px; margin-bottom: 8px; }}
                .news-title {{ font-size: 16px; font-weight: bold; margin: 8px 0; color: #222; }}
                .news-content {{ font-size: 14px; color: #555; margin: 10px 0; line-height: 1.6; }}
                .news-link {{ display: inline-block; margin-top: 10px; }}
                .news-link a {{ color: #2aa198; text-decoration: none; font-weight: bold; }}
                .news-link a:hover {{ text-decoration: underline; }}
                .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📰 今日新聞摘要</h1>
                    <p>{now}</p>
                </div>
        """

        for i, article in enumerate(email_articles, 1):
            email_html += f"""
                <div class="news-item">
                    <span class="news-category">{html.escape(article['category'])}</span>
                    <div class="news-title">{i}. {html.escape(article['title'])}</div>
                    <div class="news-content">{html.escape(article['key_points'])}</div>
                    <div class="news-link"><a href="{html.escape(article['link'])}" target="_blank">閱讀完整文章 →</a></div>
                </div>
            """

        email_html += """
                <div class="footer">
                    <p>ECHO TERMINAL News Summary | 每日自動生成</p>
                </div>
            </div>
        </body>
        </html>
        """

        # 發送 Email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"📰 今日新聞摘要 {now}"
        msg['From'] = gmail_user
        msg['To'] = recipient

        msg.attach(MIMEText(email_html, 'html', 'utf-8'))

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, recipient, msg.as_string())
        server.quit()

        print(f"✓ 已成功寄送新聞摘要到 {recipient}")
    except Exception as e:
        print(f"✗ 寄送 Email 失敗: {e}")

if __name__ == "__main__":
    print("載入資料庫...")
    db = load_db()
    seen = set()
    for news in db:
        seen |= dedup_keys(news['original_link'], news.get('original_title', ''))

    print("開始抓取新聞...")
    new_raw_news = fetch_news(seen)

    new_processed = []
    if not new_raw_news:
        print("沒有新的新聞需要處理。")
    else:
        print(f"發現 {len(new_raw_news)} 則新新聞，開始由 Gemini 處理...")
        new_processed = process_news_with_gemini(new_raw_news)
        db.extend(new_processed)
        print("儲存資料庫...")
        save_db(db)

    # 重新產生網頁檔案
    print("重新產生網頁檔案...")
    generate_html(db)

    # 寄送今日新聞摘要 Email
    print("準備寄送新聞摘要 Email...")
    send_daily_email(new_processed)

    print("完成！")
