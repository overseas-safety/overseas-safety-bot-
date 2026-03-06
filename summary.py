import os
import sqlite3
import feedparser
from atproto import Client, client_utils
import deepl
import tweepy
import requests
from dotenv import load_dotenv

load_dotenv()

# 主なニュースフィード
FEEDS = [
    "http://feeds.bbci.co.uk/news/world/rss.xml", # BBC
    "https://www.aljazeera.com/xml/rss/all.xml", # Al Jazeera
]

def translate_text(text):
    auth_key = os.getenv("DEEPL_AUTH_KEY")
    if not auth_key:
        return text
    try:
        translator = deepl.Translator(auth_key)
        # 短く要約するために少し意訳指示を足す（API側の仕様内）
        return translator.translate_text(text, target_lang="JA").text
    except:
        return text

def main():
    handle = os.getenv("BLUESKY_HANDLE")
    password = os.getenv("BLUESKY_PASSWORD")
    if not handle or not password:
        print("Credentials missing.")
        return

    client = Client()
    client.login(handle, password)
    
    # BBCとAljazeeraから最新の見出しを3件ずつ抽出
    headlines = []
    
    for url in FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]: # 上位3件
            headlines.append(entry.title)
    
    # 全部で6件のヘッドラインを日本語に翻訳
    translated_lines = []
    for i, title in enumerate(headlines[:5]): # 長すぎないように5件で絞る
        j_title = translate_text(title)
        translated_lines.append(f"・{j_title}")
        
    summary_text = "🌍【世界の主要ヘッドライン定時まとめ】\n\n" + "\n".join(translated_lines) + "\n\n#国際情勢まとめ #ニュース"
    
    print("-" * 30)
    print(summary_text)
    
    # 投稿！
    try:
        post = client.send_post(summary_text)
        print("Summary posted successfully to Bluesky!")
    except Exception as e:
        print(f"Failed to post summary to Bluesky: {e}")

    # Xへの投稿
    api_key = os.getenv("X_API_KEY")
    api_secret = os.getenv("X_API_SECRET")
    access_token = os.getenv("X_ACCESS_TOKEN")
    access_secret = os.getenv("X_ACCESS_TOKEN_SECRET")
    
    if all([api_key, api_secret, access_token, access_secret]):
        try:
            x_client = tweepy.Client(
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_secret
            )
            x_client.create_tweet(text=summary_text)
            print("Summary posted successfully to X!")
        except Exception as e:
            print(f"Failed to post summary to X: {e}")
    else:
        print("X credentials missing in summary.py")

    # Telegramへの投稿
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    tg_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if all([tg_token, tg_chat_id]):
        try:
            url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
            payload = {"chat_id": tg_chat_id, "text": summary_text}
            requests.post(url, json=payload)
            print("Summary posted successfully to Telegram!")
        except Exception as e:
            print(f"Failed to post summary to Telegram: {e}")
    else:
        print("Telegram credentials missing in summary.py")

if __name__ == "__main__":
    main()
