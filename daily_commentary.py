import os
import feedparser
from atproto import Client, client_utils
import tweepy
import requests
from google import genai
from dotenv import load_dotenv

load_dotenv()

# 主なニュースフィードから1つ選ぶ用
FEED_URL = "http://feeds.bbci.co.uk/news/world/rss.xml"

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
以下の海外ニュースの見出しを元に、国際情勢や海外渡航への影響を地政学アナリストとして80文字以内で解説してください。見出し: {title}
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
    base_text = f"💡正午の深掘り解説\n「{short_title}」\n\n{commentary}\n\n詳細: {link}"
    
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
            bluesky_builder.link("有事速報はTelegramへ", "https://t.me/kaigai_anzen")
            bluesky_builder.text("\n#地政学リスク #海外安全")
            
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
            x_text = base_text + "\n\n👇日々の平時ニュースはBlueskyでも発信中\nhttps://bsky.app/profile/overseassafetyjp.bsky.social\n\n#地政学リスク #海外安全 #ニュース解説"
            x_client = tweepy.Client(
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_secret
            )
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
