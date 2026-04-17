import feedparser
from google import genai
import os
import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlparse, urlunparse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import markdown
import re

# 設定檔案路徑
DB_DIR = "data"
DB_PATH = os.path.join(DB_DIR, "news.json")
CONTENT_DIR = "content"
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

def fetch_news(existing_links, existing_titles):
    """抓取 RSS 中的新聞清單 (過濾已存在的新聞)"""
    all_news = []

    manual_url = os.getenv("MANUAL_URL")
    if manual_url:
        cleaned_manual = clean_url(manual_url)
        if cleaned_manual not in existing_links:
            print(f"偵測到手動網址: {manual_url}")
            manual_news = fetch_manual_url(manual_url)
            if manual_news:
                all_news.append(manual_news)

    for category, url in FEEDS.items():
        print(f"正在抓取 {category} RSS...")
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            cleaned_link = clean_url(entry.link)
            short_title = entry.title[:20]
            if cleaned_link not in existing_links and short_title not in existing_titles:
                all_news.append({
                    "category": category,
                    "title": entry.title,
                    "link": entry.link,
                    "summary": entry.summary if hasattr(entry, 'summary') else ""
                })
            else:
                print(f"   跳過重複新聞: {entry.title[:30]}...")

    # 抓取新增的電子報來源
    print("正在抓取 TLDR Newsletter...")
    tldr_news = fetch_tldr()
    for news in tldr_news:
        cleaned_link = clean_url(news['link'])
        short_title = news['title'][:20]
        if cleaned_link not in existing_links and short_title not in existing_titles:
            all_news.append(news)
        else:
            print(f"   跳過重複新聞: {news['title'][:30]}...")

    print("正在抓取 1440 Daily Digest...")
    digest_news = fetch_1440()
    for news in digest_news:
        cleaned_link = clean_url(news['link'])
        short_title = news['title'][:20]
        if cleaned_link not in existing_links and short_title not in existing_titles:
            all_news.append(news)
        else:
            print(f"   跳過重複新聞: {news['title'][:30]}...")

    print("正在抓取 The Rundown AI...")
    rundown_news = fetch_rundown()
    for news in rundown_news:
        cleaned_link = clean_url(news['link'])
        short_title = news['title'][:20]
        if cleaned_link not in existing_links and short_title not in existing_titles:
            all_news.append(news)
        else:
            print(f"   跳過重複新聞: {news['title'][:30]}...")

    print("正在抓取 Los Altos 當地新聞...")
    los_altos_news = fetch_los_altos()
    for news in los_altos_news:
        cleaned_link = clean_url(news['link'])
        short_title = news['title'][:20]
        if cleaned_link not in existing_links and short_title not in existing_titles:
            all_news.append(news)
        else:
            print(f"   跳過重複新聞: {news['title'][:30]}...")

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
                model="gemini-2.5-flash-lite",
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

def generate_html(all_history, tech_articles=[]):
    """產生具有清爽白色 Terminal 風格的 Echo Terminal 網頁"""
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

    # 生成技術專欄 HTML
    tech_section_html = ""
    if tech_articles:
        tech_section_html = """
        <section class="tech-column">
            <h2 class="section-title">⏱️ 挑戰 1 分鐘系列</h2>
            <div class="tech-grid">
        """
        for article in tech_articles:
            tech_section_html += f"""
                <a href="{article['link']}" class="tech-card">
                    <div class="tech-tag">TECH_LAB</div>
                    <div class="tech-title">{article['title']}</div>
                    <div class="tech-date">{article['date']}</div>
                </a>
            """
        tech_section_html += """
            </div>
        </section>
        <hr style="border: 0; border-top: 1px solid var(--border-color); margin: 40px 0;">
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Echo Terminal | Intelligence Briefing</title>
        <style>
            :root {{
                --bg-color: #ffffff;
                --card-bg: #f8f9fa;
                --text-main: #495057;
                --text-muted: #adb5bd;
                --accent-color: #2aa198;
                --terminal-dark: #212529;
                --border-color: #e9ecef;

            }}
            body {{
                font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', Courier, monospace, 'PingFang TC';
                line-height: 1.8;
                background-color: var(--bg-color);
                color: var(--text-main);
                max-width: 850px;
                margin: 0 auto;
                padding: 50px 25px;
            }}
            header {{
                border-bottom: 2px solid var(--accent-color);
                padding-bottom: 25px;
                margin-bottom: 45px;
            }}
            h1 {{
                font-size: 2.8rem;
                margin: 0;
                color: var(--terminal-dark);
                letter-spacing: -1.5px;
                font-weight: 800;
            }}
            .tagline {{
                color: var(--text-muted);
                font-size: 0.9rem;
                margin-top: 8px;
            }}
            .status-bar {{
                font-size: 0.8rem;
                color: var(--accent-color);
                margin-top: 15px;
                background: rgba(5, 118, 66, 0.05);
                padding: 6px 18px;
                border-radius: 6px;
                display: inline-block;
                border: 1px solid rgba(5, 118, 66, 0.1);
            }}
            .section-title {{
                font-size: 1.2rem;
                color: var(--terminal-dark);
                margin-bottom: 20px;
                font-weight: bold;
            }}
            .tech-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .tech-card {{
                background: var(--card-bg);
                padding: 20px;
                border: 1px solid var(--border-color);
                border-radius: 6px;
                text-decoration: none;
                color: var(--text-main);
                transition: all 0.2s;
            }}
            .tech-card:hover {{
                border-color: var(--accent-color);
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            }}
            .tech-tag {{
                font-size: 0.7rem;
                color: var(--accent-color);
                font-weight: bold;
                margin-bottom: 8px;
            }}
            .tech-title {{
                font-size: 1rem;
                font-weight: bold;
                line-height: 1.4;
                margin-bottom: 10px;
            }}
            .tech-date {{
                font-size: 0.75rem;
                color: var(--text-muted);
            }}
            .news-card {{
                background: var(--card-bg);
                padding: 35px;
                margin-bottom: 40px;
                border-radius: 8px;
                border: 1px solid var(--border-color);
                box-shadow: 0 2px 15px rgba(0,0,0,0.05);
                transition: transform 0.2s, background 0.2s;
            }}
            .news-card:hover {{
                transform: translateX(5px);
                background: #f1f3f5;
            }}
            .category-tag {{
                background: var(--accent-color);
                color: #fff;
                padding: 2px 12px;
                border-radius: 4px;
                font-size: 0.75rem;
                font-weight: bold;
            }}
            .timestamp {{
                float: right;
                color: var(--text-muted);
                font-size: 0.8rem;
            }}
            .news-content {{
                margin-top: 25px;
                white-space: pre-wrap;
                color: var(--text-main);
                font-size: 1.1rem;
            }}
            a.origin-link {{
                display: inline-block;
                margin-top: 25px;
                color: var(--accent-color);
                text-decoration: none;
                font-size: 0.95rem;
                font-weight: bold;
                border: 1px solid var(--accent-color);
                padding: 6px 20px;
                border-radius: 4px;
            }}
            a.origin-link:hover {{
                background: var(--accent-color);
                color: #fff;
            }}
            footer {{
                text-align: center;
                color: var(--text-muted);
                font-size: 0.85rem;
                margin-top: 100px;
                padding-top: 30px;
                border-top: 1px solid var(--border-color);
            }}
            .cursor {{
                display: inline-block;
                width: 12px;
                height: 1.1em;
                background: var(--accent-color);
                vertical-align: middle;
                margin-left: 8px;
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
            <div class="tagline">Neural Information System // Clean Briefing Interface</div>
            <div class="status-bar">STATUS: OPTIMAL | DATABASE_SIZE: {len(all_history)} | SYNC_TIME: {now}</div>
        </header>
        
        <main>
            {tech_section_html}
    """
    
    for news in display_news:
        html_content += f"""
        <article class="news-card">
            <span class="category-tag">{news['category']}</span>
            <span class="timestamp">LOG_REF: {news.get('timestamp', '')}</span>
            <div class="news-content">{news['content']}</div>
            <a href="{news['original_link']}" class="origin-link" target="_blank">DECODE_FULL_SOURCE_CONTENT →</a>
        </article>
        """
    
    html_content += """
        </main>
        <footer>
            ECHO TERMINAL v2.3 // CLEAN WHITE INTERFACE // 2026
        </footer>
    </body>
    </html>
    """
    
    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

def process_markdown_articles():
    """掃描 content/tech 目錄下的 .md 檔案，並轉換為個別 HTML 檔案"""
    tech_content_dir = os.path.join(CONTENT_DIR, "tech")
    tech_docs_dir = os.path.join(DOCS_DIR, "tech")
    
    if not os.path.exists(tech_content_dir):
        print(f"找不到目錄: {tech_content_dir}，跳過 Markdown 處理。")
        return []

    os.makedirs(tech_docs_dir, exist_ok=True)
    
    # 找到所有的 .md 檔案
    md_files = sorted([f for f in os.listdir(tech_content_dir) if f.endswith(".md")], reverse=True)
    if not md_files:
        print("在 content/tech 中找不到任何 .md 檔案。")
        return []

    processed_articles = []
    for md_file in md_files:
        md_file_path = os.path.join(tech_content_dir, md_file)
        html_filename = md_file.replace(".md", ".html")
        html_file_path = os.path.join(tech_docs_dir, html_filename)
        
        print(f"正在處理 Markdown 檔案: {md_file_path}...")

        with open(md_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 解析 Front Matter (YAML 格式)
        title = "技術教學"
        date_str = ""
        markdown_body = content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                front_matter = parts[1]
                markdown_body = parts[2]
                
                # 簡單的正則表達式解析（支持有無引號）
                title_match = re.search(r'title:\s*["\']?(.*?)["\']?\s*$', front_matter, re.MULTILINE)
                if title_match:
                    title = title_match.group(1).strip()
                
                date_match = re.search(r'date:\s*(.*)', front_matter)
                if date_match:
                    date_str = date_match.group(1).strip()

        # 移除 Markdown body 中可能與 Front Matter 重複的標題 (以 # 開頭的第一行)
        markdown_body = markdown_body.lstrip()
        if markdown_body.startswith("# "):
            lines = markdown_body.split("\n", 1)
            if len(lines) > 1:
                markdown_body = lines[1].lstrip()
            else:
                markdown_body = ""

        # 將 Markdown 轉換為 HTML
        html_body = markdown.markdown(markdown_body, extensions=['extra', 'codehilite'])

        # 生成完整的 HTML 頁面 (延用首頁風格)
        full_html = f"""
        <!DOCTYPE html>
        <html lang="zh-TW">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title} | Echo Terminal</title>
            <style>
                :root {{
                    --bg-color: #ffffff;
                    --card-bg: #f8f9fa;
                    --text-main: #495057;
                    --text-muted: #adb5bd;
                    --accent-color: #2aa198;
                    --terminal-dark: #212529;
                    --border-color: #e9ecef;
                }}
                body {{
                    font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', Courier, monospace, 'PingFang TC';
                    line-height: 1.8;
                    background-color: var(--bg-color);
                    color: var(--text-main);
                    max-width: 850px;
                    margin: 0 auto;
                    padding: 50px 25px;
                }}
                header {{
                    border-bottom: 2px solid var(--accent-color);
                    padding-bottom: 25px;
                    margin-bottom: 45px;
                }}
                .back-home {{
                    margin-bottom: 20px;
                    display: block;
                    color: var(--accent-color);
                    text-decoration: none;
                    font-weight: bold;
                }}
                h1 {{
                    font-size: 2.2rem;
                    margin: 0;
                    color: var(--terminal-dark);
                    letter-spacing: -1px;
                    font-weight: 800;
                }}
                .article-meta {{
                    color: var(--text-muted);
                    font-size: 0.9rem;
                    margin-top: 10px;
                }}
                .content {{
                    margin-top: 40px;
                    color: var(--text-main);
                    font-size: 1.1rem;
                }}
                .content h2 {{ color: var(--terminal-dark); border-bottom: 1px solid var(--border-color); padding-bottom: 10px; }}
                .content pre {{ background: #f1f3f5; padding: 20px; border-radius: 6px; overflow-x: auto; }}
                .content code {{ font-family: 'Fira Code', monospace; color: #d63384; }}
                footer {{
                    text-align: center;
                    color: var(--text-muted);
                    font-size: 0.85rem;
                    margin-top: 100px;
                    padding-top: 30px;
                    border-top: 1px solid var(--border-color);
                }}
            </style>
        </head>
        <body>
            <header>
                <a href="../index.html" class="back-home">← BACK_TO_ECHO_TERMINAL</a>
                <h1>{title}</h1>
                <div class="article-meta">PUBLISHED: {date_str}</div>
            </header>
            
            <article class="content">
                {html_body}
            </article>
            
            <footer>
                ECHO TERMINAL v2.3 // TECH TUTORIALS // 2026
            </footer>
        </body>
        </html>
        """
        
        with open(html_file_path, "w", encoding="utf-8") as f:
            f.write(full_html)
        
        processed_articles.append({
            "title": title,
            "date": date_str.split("T")[0] if "T" in date_str else date_str,
            "link": f"tech/{html_filename}"
        })
        print(f"✓ 已成功將 {md_file} 轉換為 HTML")
    
    return processed_articles

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
                    <span class="news-category">{article['category']}</span>
                    <div class="news-title">{i}. {article['title']}</div>
                    <div class="news-content">{article['key_points']}</div>
                    <div class="news-link"><a href="{article['link']}" target="_blank">閱讀完整文章 →</a></div>
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
    existing_links = {clean_url(news['original_link']) for news in db}
    existing_titles = {news.get('original_title', '')[:20] for news in db}

    print("開始抓取新聞...")
    new_raw_news = fetch_news(existing_links, existing_titles)

    new_processed = []
    if not new_raw_news:
        print("沒有新的新聞需要處理。")
    else:
        print(f"發現 {len(new_raw_news)} 則新新聞，開始由 Gemini 處理...")
        new_processed = process_news_with_gemini(new_raw_news)
        db.extend(new_processed)
        print("儲存資料庫...")
        save_db(db)

    # 處理技術專欄 Markdown 檔案
    print("開始處理技術專欄 Markdown...")
    tech_articles = process_markdown_articles()

    print("重新產生網頁檔案...")
    generate_html(db, tech_articles)

    # 寄送今日新聞摘要 Email
    print("準備寄送新聞摘要 Email...")
    send_daily_email(new_processed)

    print("完成！")
