import json
import os
import random
import smtplib
from google import genai
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 加載環境變數
def load_config():
    config = {}
    dot_env_path = ".env"
    if os.path.exists(dot_env_path):
        with open(dot_env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    key, value = line.strip().split("=", 1)
                    config[key.strip()] = value.strip().replace('"', '')
    return config

def send_email(config, subject, body):
    gmail_user = config.get("GMAIL_USER")
    gmail_password = config.get("GMAIL_APP_PASSWORD")
    recipient = config.get("RECIPIENT_EMAIL")

    if not all([gmail_user, gmail_password, recipient]):
        print("Skipping email: Gmail configuration missing in .env")
        return

    msg = MIMEMultipart()
    msg['From'] = f"AI Morning DJ <{gmail_user}>"
    msg['To'] = recipient
    msg['Subject'] = subject

    # 簡單地將內容放入郵件中
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(gmail_user, gmail_password)
        server.send_message(msg)
        server.close()
        print(f"Email sent successfully to {recipient}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def get_latest_news(news_file):
    if not os.path.exists(news_file):
        return "No news data found."
    with open(news_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return "\n".join([item['content'][:500] for item in data[:3]])

def get_music_list(music_file):
    if not os.path.exists(music_file):
        return []
    with open(music_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def morning_dj():
    config = load_config()
    
    api_key = config.get("GOOGLE_API_KEY")
    obsidian_inbox = config.get("OBSIDIAN_INBOX")
    news_file = config.get("NEWS_DATA_FILE")
    music_file = config.get("MUSIC_HISTORY_FILE")

    if not api_key:
        print("Error: GOOGLE_API_KEY not found in .env.")
        return

    client = genai.Client(api_key=api_key)

    news_summary = get_latest_news(news_file)
    music_list = get_music_list(music_file)
    
    if not music_list:
        print("Error: Music list is empty or not found.")
        return

    sample_music = random.sample(music_list, min(15, len(music_list)))
    music_context = "\n".join([f"- {m['title']} by {m['artist']} (Link: https://music.youtube.com/watch?v={m['video_id']})" for m in sample_music])

    prompt = f"""
    你是 Erin 的私人 AI DJ。你的任務是讀取今天的【新聞內容】，並從【備選歌單】中挑選一首最適合今天心情或能給予力量的歌。

    【今日新聞摘要】：
    {news_summary}

    【備選歌單】：
    {music_context}

    請撰寫一份給 Erin 的 Morning DJ 報告，包含：
    1. 針對今天新聞的感言（溫暖、有洞見，不超過 100 字）。
    2. 推薦歌曲名稱與歌手。
    3. YouTube Music 連結。
    4. 推薦原因：為什麼這首歌適合今天的新聞氛圍？或是它能如何療癒今天的心情？

    請直接輸出內容，不要帶有額外的 Markdown 標籤語法在最外層。
    """

    response = client.models.generate_content(
        model='gemini-2.5-flash-lite',
        contents=prompt
    )
    report_content = response.text
    
    # 1. 儲存到 Obsidian
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"Morning-DJ-{today}.md"
    file_path = os.path.join(obsidian_inbox, filename)
    os.makedirs(obsidian_inbox, exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f"# 📻 Morning DJ Radio - {today}\n\n")
        f.write(report_content)
    print(f"Obsidian note created at: {file_path}")

    # 2. 同步發送 Email
    subject = f"📻 Your Morning DJ Report - {today}"
    email_body = f"Good morning Erin!\n\nHere is your daily news and music pairing:\n\n{report_content}"
    send_email(config, subject, email_body)

if __name__ == "__main__":
    morning_dj()
