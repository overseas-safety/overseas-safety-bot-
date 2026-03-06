import os
from atproto import Client
from main import post_to_bluesky, post_to_x, post_to_telegram
from dotenv import load_dotenv

load_dotenv()

def run_test():
    # 本番と同じフォーマットで架空の特大ニュースを作成
    title = "イラン首都近郊で大規模な爆発音、政府機能が一部停止との報道 (※こちらはシステム稼働テストです)"
    link = "https://travel.state.gov/content/travel/en/traveladvisories/traveladvisories.html"
    is_emergency = True
    original_title = "Iran massive explosion reported near capital, infrastructure down" # "explosion" を含むためポータブル電源のアフィリエイトが反応するかテスト
    
    print("Testing Telegram...")
    post_to_telegram(title, link, is_emergency, original_title)
    
    print("Testing Bluesky...")
    client = Client()
    handle = os.getenv("BLUESKY_HANDLE")
    password = os.getenv("BLUESKY_PASSWORD")
    if handle and password:
        client.login(handle, password)
        post_to_bluesky(client, title, link, is_emergency, original_title)
    else:
        print("No bluesky credentials")
        
    print("Testing X...")
    post_to_x(title, link, is_emergency, original_title)

if __name__ == "__main__":
    run_test()
