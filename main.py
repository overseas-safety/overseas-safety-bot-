import os
import sqlite3
import feedparser
from atproto import Client, client_utils, models
import deepl
from dotenv import load_dotenv

# Load environment variables for local testing
load_dotenv()

# RSS Feed for US Department of State Travel Advisories
RSS_URL = "https://travel.state.gov/_res/rss/TAsTWs.xml"

# DB Setup for tracking posted alerts
DB_FILE = "posted_alerts.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS alerts
                 (link TEXT PRIMARY KEY)''')
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

def fetch_latest_alerts():
    feed = feedparser.parse(RSS_URL)
    alerts = []
    for entry in feed.entries:
        if not is_posted(entry.link):
            alerts.append({
                "title": entry.title,
                "link": entry.link,
            })
    return alerts

def translate_text(text):
    auth_key = os.getenv("DEEPL_AUTH_KEY")
    if not auth_key:
        print("Warning: DEEPL_AUTH_KEY not set. Using original text.")
        return text
        
    try:
        translator = deepl.Translator(auth_key)
        result = translator.translate_text(text, target_lang="JA")
        return result.text
    except Exception as e:
        print(f"Translation error: {e}")
        return text

def post_to_bluesky(title, link, is_emergency=False):
    handle = os.getenv("BLUESKY_HANDLE")
    password = os.getenv("BLUESKY_PASSWORD")
    
    if not all([handle, password]):
        print("Warning: BLUESKY_HANDLE or BLUESKY_PASSWORD not set. Skipping actual post.")
        return False
        
    try:
        client = Client()
        client.login(handle, password)
        
        # Build facet for the link (clickable URL)
        text_builder = client_utils.TextBuilder()
        
        if is_emergency:
            text_builder.text(f"🔴【緊急：中東情勢速報】🔴\n{title}\n\n⚠️周辺状況にご注意ください。\n詳細:\n")
            text_builder.link(link, link)
            text_builder.text("\n\n#イラン情勢 #中東速報 #緊急アラート")
        else:
            text_builder.text(f"🚨【海外安全速報】\n{title}\n\n詳細はこちら:\n")
            text_builder.link(link, link)
            text_builder.text("\n\n#海外安全 #渡航情報")
        
        post = client.send_post(text_builder)
        print("Successfully posted to Bluesky.")
        
        # Affiliate reply if it's an emergency
        if is_emergency:
            reply_builder = client_utils.TextBuilder()
            reply_builder.text("💡【渡航中の備え・通信確保】\n現地での通信制限や情報統制に備え、渡航用VPNのご準備を強く推奨します（※日本からのみアクセス可能な安否確認サイトがある場合などに役立ちます）:\n\n👉 ")
            reply_builder.link("おすすめのVPN比較・登録はこちら(※アフィリエイトリンクに変更してください)", "https://example.com/vpn-affiliate-link")
            
            root_ref = models.ComAtprotoRepoStrongRef.Main(cid=post.cid, uri=post.uri)
            reply_ref = models.AppBskyFeedPost.ReplyRef(parent=root_ref, root=root_ref)
            
            client.send_post(reply_builder, reply_to=reply_ref)
            print("Successfully replied with affiliate link.")
            
        return True
    except Exception as e:
        print(f"Bluesky Post error: {e}")
        return False

def main():
    print("Starting Overseas Safety Alert Bot (Emergency Mode enabled)...")
    init_db()
    
    alerts = fetch_latest_alerts()
    print(f"Found {len(alerts)} new alert(s).")
    
    # Emergency keywords
    emergency_keywords = ["Iran", "Israel", "Middle East", "Iraq", "Syria", "Lebanon", "Palestine"]
    
    for alert in alerts[:5]: # 只今大量の投稿を防ぐため、1回につき最大5件まで処理
        original_title = alert['title']
        link = alert['link']
        
        print(f"Processing: {original_title}")
        translated_title = translate_text(original_title)
        
        # Check if it's an emergency alert
        is_emergency = any(kw.lower() in original_title.lower() for kw in emergency_keywords)
        
        print("-" * 30)
        print("--- POST DRAFT ---")
        if is_emergency:
            print(f"🔴【緊急：中東情勢速報】🔴\n{translated_title}\n\n詳細はこちら:\n{link}\n\n#イラン情勢 #中東速報 #緊急アラート")
        else:
            print(f"🚨【海外安全速報】\n{translated_title}\n\n詳細はこちら:\n{link}\n\n#海外安全 #渡航情報")
        print("-" * 30)
        
        success = post_to_bluesky(translated_title, link, is_emergency)
        
        # Mark as posted even on failure during testing to prevent retry loops
        mark_as_posted(link)

if __name__ == "__main__":
    main()
