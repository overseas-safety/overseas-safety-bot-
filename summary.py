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

def init_db():
    conn = sqlite3.connect('alerts.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS posted_alerts
                 (url TEXT PRIMARY KEY, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def is_posted(url):
    conn = sqlite3.connect('alerts.db')
    c = conn.cursor()
    c.execute('SELECT 1 FROM posted_alerts WHERE url = ?', (url,))
    result = c.fetchone()
    conn.close()
    return bool(result)

def mark_as_posted(url):
    conn = sqlite3.connect('alerts.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO posted_alerts (url) VALUES (?)', (url,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

def translate_text(text):
    auth_key = os.getenv("DEEPL_AUTH_KEY")
    if not auth_key:
        return text
    try:
        translator = deepl.Translator(auth_key)
        # 短く要約するために少し意訳指示を足す（API側の仕様内）
        return translator.translate_text(text, target_lang="EN-US").text
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
    
    init_db()

    # 安全情報とニュースから適度に抽出（既出チェック付き）
    headlines = []
    
    for section, urls in FEEDS.items():
        for url in urls:
            feed = feedparser.parse(url)
            # 新しい記事を探すため少し深めに検索
            for entry in feed.entries[:10]: 
                if not is_posted(entry.link):
                    headlines.append({"title": entry.title, "link": entry.link})
                    # 1ソースにつき新着2件までで十分
                    if len([h for h in headlines if h["link"] == entry.link]) >= 2:
                        break
    
    # 全体から長すぎないように最大5件で絞る
    headlines = headlines[:5]
    
    if not headlines:
        print("No new headlines to summarize. Skip posting.")
        return

    # 日本語に翻訳してDBに記録
    translated_lines = []
    for item in headlines:
        j_title = translate_text(item["title"])
        translated_lines.append(f"• {j_title}")
        mark_as_posted(item["link"])
        
    base_text = "🌍 [Global Headlines Summary]\n\n" + "\n".join(translated_lines)
    
    # Bluesky用の動的ビルダーを構成（自社商品＋Telegramリンク）
    bluesky_builder = client_utils.TextBuilder()
    bluesky_builder.text(base_text + "\n\n🔒 ")
    bluesky_builder.link("Personal & Business Security Guides", "https://security-products.vercel.app/")
    bluesky_builder.text("\n📲 ")
    bluesky_builder.link("Get instant alerts on Telegram", "https://t.me/kaigai_anzen")
    bluesky_builder.text("\n#Geopolitics #GlobalNews")
    
    print("-" * 30)
    print("Preparing summary posts...")
    
    # Blueskyへ投稿
    try:
        post = client.send_post(bluesky_builder)
        print("Summary posted successfully to Bluesky!")
    except Exception as e:
        print(f"Failed to post summary to Bluesky: {e}")

    # Xへの投稿（自社商品＋Bluesky送客）
    x_text = base_text + "\n\n🔒 Personal & Business Security Guides\nhttps://security-products.vercel.app/\n\n👇 Follow us on Bluesky for regular updates\nhttps://bsky.app/profile/overseassafetyjp.bsky.social"
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
    tg_text = base_text + "\n\n🔒 Personal & Business Security Guides\nhttps://security-products.vercel.app/\n\n🕊 Regular updates on Bluesky:\nhttps://bsky.app/profile/overseassafetyjp.bsky.social"
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
