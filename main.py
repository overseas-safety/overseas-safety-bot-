import os
import sqlite3
import feedparser
from atproto import Client, client_utils, models
import deepl
import tweepy
import requests
from dotenv import load_dotenv

load_dotenv()

DB_FILE = "posted_alerts.db"

# 1. 巡回するRSSフィードのリスト（種類分け）
FEEDS = {
    "safety": [
        "https://travel.state.gov/_res/rss/TAsTWs.xml", # 米国務省
        "https://www.anzen.mofa.go.jp/info/anzen_rss.xml" # 日本外務省
    ],
    "news": [
        "http://feeds.bbci.co.uk/news/world/rss.xml", # BBC World
        "http://rss.cnn.com/rss/edition_world.rss", # CNN World
        "https://www.aljazeera.com/xml/rss/all.xml", # Al Jazeera
        "https://news.yahoo.co.jp/rss/categories/world.xml", # Yahoo(共同/時事などの国際)
    ]
}

# 2. 緊急検知キーワード（この単語があれば「発生」として扱う）
EMERGENCY_KEYWORDS = [
    "iran", "israel", "middle east", "iraq", "lebanon", "syria", "palestine",
    "breaking", "war", "attack", "missile", "strike", "explosion",
    "武力衝突", "ミサイル", "空爆", "攻撃", "爆発", "退避", "緊急", "テロ", "渡航中止"
]

# 3. アフィリエイトリンクの振り分け用キーワード
POWER_KEYWORDS = ["explosion", "strike", "disaster", "爆発", "空爆", "インフラ", "停電"]
VPN_KEYWORDS = ["iran", "israel", "middle east", "russia", "china", "制限", "通信", "統制"]

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS alerts (link TEXT PRIMARY KEY)''')
    conn.commit()
    conn.close()

def is_posted(link):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT 1 FROM alerts WHERE link=?", (link,))
    result = c.fetchone()
    conn.close()
    return result is not None

def mark_as_posted(link):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO alerts (link) VALUES (?)", (link,))
    conn.commit()
    conn.close()

def translate_text(text):
    auth_key = os.getenv("DEEPL_AUTH_KEY")
    if not auth_key:
        return text
    try:
        translator = deepl.Translator(auth_key)
        return translator.translate_text(text, target_lang="JA").text
    except:
        return text

def post_to_bluesky(client, title, link, is_emergency, original_title):
    text_builder = client_utils.TextBuilder()
    
    if is_emergency:
        text_builder.text(f"🔴【発生：緊急速報】🔴\n{title}\n\n⚠️現地の状況・武力衝突等にご注意ください。\n詳細:\n")
        text_builder.link(link[:40]+"...", link)
        text_builder.text("\n\n#国際情勢 #速報 #緊急アラート")
    else:
        text_builder.text(f"🚨【海外安全・渡航情報】\n{title}\n\n詳細:\n")
        text_builder.link(link[:40]+"...", link)
        text_builder.text("\n\n#海外安全 #最新ニュース")
    
    try:
        post = client.send_post(text_builder)
        print("Successfully posted article.")
        
        # 動的アフィリエイトリプライ
        if is_emergency:
            original_lower = original_title.lower()
            reply_builder = client_utils.TextBuilder()
            
            # ポータブル電源が適している場合
            if any(k in original_lower for k in POWER_KEYWORDS):
                reply_builder.text("💡【有事の備え・インフラ停止対策】\n現地のインフラ破壊や突発的な停電に備え、ポータブル電源の確保・確認を強く推奨します:\n\n👉 ")
                reply_builder.link("防災・有事対応ポータブル電源の詳細", "https://px.a8.net/svt/ejp?a8mat=4AZA48+1BMP6A+4NJ4+63OY9")
            # デフォルトはVPN
            else:
                reply_builder.text("💡【有事の備え・通信ルート確保】\n現地での通信制限や情報統制に備え、日本の情報にアクセスできるVPNのご準備を強く推奨します:\n\n👉 ")
                reply_builder.link("スイカVPN（通信制限対策）の詳細", "https://px.a8.net/svt/ejp?a8mat=4AZA47+G3ASDU+4R3G+631SX")
            
            root_ref = models.ComAtprotoRepoStrongRef.Main(cid=post.cid, uri=post.uri)
            reply_ref = models.AppBskyFeedPost.ReplyRef(parent=root_ref, root=root_ref)
            client.send_post(reply_builder, reply_to=reply_ref)
            print("Successfully replied with affiliate link.")
            
        return True
    except Exception as e:
        print(f"Error post: {e}")
        return False

def post_to_x(title, link, is_emergency, original_title):
    api_key = os.getenv("X_API_KEY")
    api_secret = os.getenv("X_API_SECRET")
    access_token = os.getenv("X_ACCESS_TOKEN")
    access_secret = os.getenv("X_ACCESS_TOKEN_SECRET")
    
    if not all([api_key, api_secret, access_token, access_secret]):
        print("X API credentials missing. Skipping X.")
        return False
        
    try:
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret
        )
        
        if is_emergency:
            tweet_text = f"🔴【発生：緊急速報】🔴\n{title}\n\n⚠️現地の状況・武力衝突等にご注意ください。\n詳細:\n{link}\n\n#国際情勢 #速報 #緊急アラート"
        else:
            tweet_text = f"🚨【海外安全・渡航情報】\n{title}\n\n詳細:\n{link}\n\n#海外安全 #最新ニュース"
            
        response = client.create_tweet(text=tweet_text)
        print("Successfully posted article to X.")
        
        # 動的アフィリエイトリプライ
        if is_emergency and response.data and 'id' in response.data:
            tweet_id = response.data['id']
            original_lower = original_title.lower()
            
            if any(k in original_lower for k in POWER_KEYWORDS):
                reply_text = "💡【有事の備え・インフラ停止対策】\n現地のインフラ破壊や突発的な停電に備え、ポータブル電源の確保・確認を強く推奨します:\n\n👉 https://px.a8.net/svt/ejp?a8mat=4AZA48+1BMP6A+4NJ4+63OY9"
            else:
                reply_text = "💡【有事の備え・通信ルート確保】\n現地での通信制限や情報統制に備え、日本の情報にアクセスできるVPNのご準備を強く推奨します:\n\n👉 https://px.a8.net/svt/ejp?a8mat=4AZA47+G3ASDU+4R3G+631SX"
                
            client.create_tweet(text=reply_text, in_reply_to_tweet_id=tweet_id)
            print("Successfully replied with affiliate link on X.")
            
        return True
    except Exception as e:
        print(f"Error posting to X: {e}")
        return False

def post_to_telegram(title, link, is_emergency, original_title):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not all([bot_token, chat_id]):
        print("Telegram credentials missing. Skipping Telegram.")
        return False
        
    try:
        if is_emergency:
            text = f"🔴【発生：緊急速報】🔴\n{title}\n\n⚠️現地の状況・武力衝突等にご注意ください。\n詳細:\n{link}\n\n#国際情勢 #速報 #緊急アラート"
        else:
            text = f"🚨【海外安全・渡航情報】\n{title}\n\n詳細:\n{link}\n\n#海外安全 #最新ニュース"
            
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("Successfully posted article to Telegram.")
        
        # 動的アフィリエイトリプライ
        if is_emergency:
            original_lower = original_title.lower()
            if any(k in original_lower for k in POWER_KEYWORDS):
                reply_text = "💡【有事の備え・インフラ停止対策】\n現地のインフラ破壊や突発的な停電に備え、ポータブル電源の確保・確認を強く推奨します:\n\n👉 https://px.a8.net/svt/ejp?a8mat=4AZA48+1BMP6A+4NJ4+63OY9"
            else:
                reply_text = "💡【有事の備え・通信ルート確保】\n現地での通信制限や情報統制に備え、日本の情報にアクセスできるVPNのご準備を強く推奨します:\n\n👉 https://px.a8.net/svt/ejp?a8mat=4AZA47+G3ASDU+4R3G+631SX"
                
            reply_payload = {
                "chat_id": chat_id,
                "text": reply_text,
                "reply_to_message_id": response.json()["result"]["message_id"]
            }
            requests.post(url, json=reply_payload)
            print("Successfully replied with affiliate link on Telegram.")
            
        return True
    except Exception as e:
        print(f"Error posting to Telegram: {e}")
        return False

def main():
    handle = os.getenv("BLUESKY_HANDLE")
    password = os.getenv("BLUESKY_PASSWORD")
    if not handle or not password:
        print("No Bluesky credentials. Exiting.")
        return

    client = Client()
    client.login(handle, password)
    
    init_db()
    
    new_alerts = []
    
    # 1. 官公庁の安全情報（すべて取得）
    for url in FEEDS["safety"]:
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:
            if not is_posted(entry.link):
                new_alerts.append({"title": entry.title, "link": entry.link, "is_emergency": False, "force_post": True})
                
    # 2. ニュースサイト（緊急キーワードが含まれるものだけ取得＝Breakingのみ）
    for url in FEEDS["news"]:
        feed = feedparser.parse(url)
        for entry in feed.entries[:15]:
            if not is_posted(entry.link):
                title_lower = entry.title.lower()
                is_emergency = any(kw in title_lower for kw in EMERGENCY_KEYWORDS)
                if is_emergency:
                    new_alerts.append({"title": entry.title, "link": entry.link, "is_emergency": True, "force_post": True})
    
    print(f"Found {len(new_alerts)} new crucial alerts.")
    
    # スパム防止（1回の実行で最大4件まで）
    for alert in new_alerts[:4]:
        orig_title = alert['title']
        link = alert['link']
        is_emg = alert['is_emergency']
        
        # 安全情報系のフィードでも、タイトルに緊急キーワードがあれば格上げ
        if not is_emg and any(kw in orig_title.lower() for kw in EMERGENCY_KEYWORDS):
            is_emg = True
            
        translated = translate_text(orig_title)
        print(f"Posting: {translated}")
        
        post_to_bluesky(client, translated, link, is_emg, orig_title)
        post_to_x(translated, link, is_emg, orig_title)
        post_to_telegram(translated, link, is_emg, orig_title)
        
        mark_as_posted(link)

if __name__ == "__main__":
    main()
