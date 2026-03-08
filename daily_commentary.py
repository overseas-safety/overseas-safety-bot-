import os
import feedparser
from atproto import Client, client_utils
import tweepy
import requests
from google import genai
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# 主なニュースフィードから1つ選ぶ用
FEED_URL = "http://feeds.bbci.co.uk/news/world/rss.xml"

# GitHub Pagesブログのインデックスファイルパス
BLOG_INDEX_FILE = "docs/index.md"

def get_top_news():
    feed = feedparser.parse(FEED_URL)
    if feed.entries:
        entry = feed.entries[0]
        return entry.title, entry.link
    return None, None

def generate_commentary(title):
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        print("GEMINI_API_KEY is not set.")
        return None
        
    client = genai.Client(api_key=gemini_key)
    
    # モデルの取得 (gemini-2.5-flashを使用)
    try:
        prompt = f"""
As a geopolitical analyst, provide a brief (under 140 characters in English) analysis of this news headline, focusing on its impact on global security or travel without any hashtags or greetings. Headline: {title}
"""
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"Failed to generate commentary: {e}")
        return None

def main():
    title, link = get_top_news()
    if not title:
        print("No news found.")
        return
        
    print(f"Top News: {title}")
    
    commentary = generate_commentary(title)
    if not commentary:
        print("Failed to generate commentary.")
        return
        
    print(f"Generated Commentary: {commentary}")
    
    # 300文字制限回避のためにリンクとタイトルを切り詰める
    short_title = title[:40] + "..." if len(title) > 40 else title
    
    # 実行時間（UTC）から日本時間の正午か夕方かを判定 -> 今はグローバルなので単に時間帯名
    now_utc_hour = datetime.utcnow().hour
    time_prefix = "Midday" if now_utc_hour < 6 else "Evening"
    
    base_text = f"💡 {time_prefix} Deep Dive\n「{short_title}」\n\n{commentary}\n\nDetails: {link}"
    
    # --- ブログ（GitHub Pages）の自動更新（SEO施策） ---
    try:
        current_date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        blog_entry = f"\n\n## {title}\n*Date: {current_date_str}*\n\n**[Expert Geopolitical Analysis]**\n> {commentary}\n\n[Read Primary Source]({link})\n"
        
        # 既存のブログファイルに最新の1件を一番上（ヘッダーの下）に追記していく
        with open(BLOG_INDEX_FILE, "r") as f:
            lines = f.readlines()
        
        insert_index = 0
        for i, line in enumerate(lines):
            if "### Latest News & Analysis" in line:
                insert_index = i + 1
                break
                
        if insert_index > 0:
            lines.insert(insert_index, blog_entry)
            with open(BLOG_INDEX_FILE, "w") as f:
                f.writelines(lines)
            print("Blog index updated successfully!")
    except Exception as e:
        print(f"Failed to update blog index: {e}")
        
    # --- Blueskyへの投稿 ---
    handle = os.getenv("BLUESKY_HANDLE")
    password = os.getenv("BLUESKY_PASSWORD")
    if handle and password:
        try:
            client = Client()
            client.login(handle, password)
            
            bluesky_builder = client_utils.TextBuilder()
            # The text includes the base_text and adds the telegram link
            bluesky_builder.text(base_text + "\n\n📲 ")
            bluesky_builder.link("Fastest Breaking Alerts on Telegram", "https://t.me/kaigai_anzen")
            bluesky_builder.text("\n#Geopolitics #TravelSafety")
            
            client.send_post(bluesky_builder)
            print("Commentary posted successfully to Bluesky!")
        except Exception as e:
            print(f"Failed to post commentary to Bluesky: {e}")
            
    # --- Xへの投稿 ---
    api_key = os.getenv("X_API_KEY")
    api_secret = os.getenv("X_API_SECRET")
    access_token = os.getenv("X_ACCESS_TOKEN")
    access_secret = os.getenv("X_ACCESS_TOKEN_SECRET")
    
    if all([api_key, api_secret, access_token, access_secret]):
        try:
            x_client = tweepy.Client(consumer_key=api_key, consumer_secret=api_secret, access_token=access_token, access_token_secret=access_secret)
            x_text = base_text + "\n\n📲 Telegram:\nhttps://t.me/kaigai_anzen\n\n#Geopolitics"
            x_client.create_tweet(text=x_text)
            print("Commentary posted successfully to X!")
        except Exception as e:
            print(f"Failed to post commentary to X: {e}")
            
    # --- Telegramへの投稿 ---
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    tg_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if all([tg_token, tg_chat_id]):
        try:
            tg_text = base_text + "\n\n🕊 日々の平時ニュースはBlueskyでも発信中:\nhttps://bsky.app/profile/overseassafetyjp.bsky.social\n\n#地政学リスク #海外安全 #ニュース解説"
            url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
            payload = {"chat_id": tg_chat_id, "text": tg_text}
            requests.post(url, json=payload)
            print("Commentary posted successfully to Telegram!")
        except Exception as e:
            print(f"Failed to post commentary to Telegram: {e}")

if __name__ == "__main__":
    main()
