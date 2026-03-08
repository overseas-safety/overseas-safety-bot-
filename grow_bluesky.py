import os
from atproto import Client
from dotenv import load_dotenv
import time

load_dotenv()

# いいね（Like）をつける対象のターゲットキーワード
# （このキーワードをつぶやいている人＝海外に行く人、リスク管理に関心がある人）
TARGET_KEYWORDS = [
    "海外出張",
    "海外旅行",
    "中東",
    "治安 悪い",
    "VPN",
    "スリ 海外"
]

def auto_engage():
    handle = os.getenv("BLUESKY_HANDLE")
    password = os.getenv("BLUESKY_PASSWORD")
    if not handle or not password:
        print("No Bluesky credentials. Exiting.")
        return

    client = Client()
    client.login(handle, password)
    print("Logged in to Bluesky for growth hacking.")

    liked_count = 0
    max_likes_per_run = 10 # 1回の実行で10件まで（スパム判定防止）

    for keyword in TARGET_KEYWORDS:
        if liked_count >= max_likes_per_run:
            break
            
        try:
            # キーワードで最新の投稿を検索 (limit=2)
            response = client.app.bsky.feed.search_posts({'q': keyword, 'limit': 2})
            
            for post in response.posts:
                if liked_count >= max_likes_per_run:
                    break
                    
                # 自分の投稿にはいいねしない
                if post.author.handle == handle:
                    continue
                    
                print(f"Engaging with {post.author.handle}: {post.record.text[:30]}...")
                try:
                    # いいねをつける
                    client.like(post.uri, post.cid)
                    # フォロバ狙いで積極的にフォローする（効果絶大）
                    client.follow(post.author.did)
                except Exception as inner_e:
                    print(f"Could not follow/like {post.author.handle}: {inner_e}")
                    
                liked_count += 1
                time.sleep(2) # 凍結防止のために間隔を空ける
                
        except Exception as e:
            print(f"Error during engagement for keyword '{keyword}': {e}")
            
    print(f"Auto engagement finished. Total engaged: {liked_count}")

if __name__ == "__main__":
    auto_engage()
