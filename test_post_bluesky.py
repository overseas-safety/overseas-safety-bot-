# test_post_bluesky.py
import os
from atproto import Client
from dotenv import load_dotenv

load_dotenv()

def main():
    handle = os.getenv("BLUESKY_HANDLE")
    password = os.getenv("BLUESKY_PASSWORD")
    
    if not handle or not password:
        print("Missing BLUESKY_HANDLE or BLUESKY_PASSWORD")
        return
        
    try:
        client = Client()
        client.login(handle, password)
        
        post = client.send_post("🚨【海外安全ボット 稼働テスト】\nこれは自動システム(Bluesky版)からの連携テスト通信です。\n\n#海外安全 #BOTテスト")
        print("Successfully posted to Bluesky!")
        print(f"URI: {post.uri}")
        
    except Exception as e:
        print(f"Failed to post to Bluesky: {e}")

if __name__ == "__main__":
    main()
