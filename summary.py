import os
import sqlite3
import feedparser
from atproto import Client, client_utils
import deepl
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
        print("Summary posted successfully!")
    except Exception as e:
        print(f"Failed to post summary: {e}")

if __name__ == "__main__":
    main()
