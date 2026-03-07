import os
import sqlite3
import feedparser
from atproto import Client, client_utils
import deepl
import tweepy
import requests
from dotenv import load_dotenv

load_dotenv()

# 巡回するRSSフィードのリスト
FEEDS = {
    "safety": [
        "https://travel.state.gov/_res/rss/TAsTWs.xml", # 米国務省
        "https://www.anzen.mofa.go.jp/info/anzen_rss.xml" # 日本外務省
    ],
    "news": [
        "http://feeds.bbci.co.uk/news/world/rss.xml", # BBC World
        "https://www.aljazeera.com/xml/rss/all.xml", # Al Jazeera
    ]
}

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
    
    # 安全情報とニュースから適度に抽出
    headlines = []
    
    for section, urls in FEEDS.items():
        for url in urls:
            feed = feedparser.parse(url)
            for entry in feed.entries[:2]: # 各ソース上位2件ずつ
                headlines.append(entry.title)
    
    # 長すぎないように最大6件で絞って日本語に翻訳
    translated_lines = []
    for i, title in enumerate(headlines[:6]):
        j_title = translate_text(title)
        translated_lines.append(f"・{j_title}")
        
    base_text = "🌍【世界の主要ヘッドライン定時まとめ】\n\n" + "\n".join(translated_lines)
    
    # Bluesky用の動的ビルダーを構成（自社商品＋Telegramリンク）
    bluesky_builder = client_utils.TextBuilder()
    bluesky_builder.text(base_text + "\n\n🔒 ")
    bluesky_builder.link("身の回りの防犯対策ガイドはこちら", "https://security-products.vercel.app/")
    bluesky_builder.text("\n📲 ")
    bluesky_builder.link("有事最速アラートはTelegram", "https://t.me/kaigai_anzen")
    bluesky_builder.text("\n#世界情勢 #海外安全")
    
    print("-" * 30)
    print("Preparing summary posts...")
    
    # Blueskyへ投稿
    try:
        post = client.send_post(bluesky_builder)
        print("Summary posted successfully to Bluesky!")
    except Exception as e:
        print(f"Failed to post summary to Bluesky: {e}")

    # Xへの投稿（自社商品＋Bluesky送客）
    x_text = base_text + "\n\n🔒 個人・ビジネス防犯対策ガイド\nhttps://security-products.vercel.app/\n\n👇日々の平時ニュースはBlueskyにて\nhttps://bsky.app/profile/overseassafetyjp.bsky.social"
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
            x_client.create_tweet(text=x_text)
            print("Summary posted successfully to X!")
        except Exception as e:
            print(f"Failed to post summary to X: {e}")
    else:
        print("X credentials missing in summary.py")

    # Telegramへの投稿（自社商品＋Bluesky送客）
    tg_text = base_text + "\n\n🔒 個人・ビジネス防犯対策ガイド\nhttps://security-products.vercel.app/\n\n🕊 平時ニュースはBlueskyにて:\nhttps://bsky.app/profile/overseassafetyjp.bsky.social"
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    tg_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if all([tg_token, tg_chat_id]):
        try:
            url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
            payload = {"chat_id": tg_chat_id, "text": tg_text}
            requests.post(url, json=payload)
            print("Summary posted successfully to Telegram!")
        except Exception as e:
            print(f"Failed to post summary to Telegram: {e}")
    else:
        print("Telegram credentials missing in summary.py")

if __name__ == "__main__":
    main()
