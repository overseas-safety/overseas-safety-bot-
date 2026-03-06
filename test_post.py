import os
import tweepy
from dotenv import load_dotenv

load_dotenv()

def post_to_x(text):
    api_key = os.getenv("X_API_KEY")
    api_secret = os.getenv("X_API_SECRET")
    access_token = os.getenv("X_ACCESS_TOKEN")
    access_secret = os.getenv("X_ACCESS_TOKEN_SECRET")
    
    try:
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret
        )
        response = client.create_tweet(text=text)
        print("Successfully posted to X.")
        print(f"Tweet ID: {response.data['id']}")
    except Exception as e:
        print(f"Failed to post: {e}")

if __name__ == "__main__":
    post_to_x("🚨【海外安全ボット 稼働テスト】\nこれは自動システムからの連携テスト通信です。\n\n#海外安全 #BOTテスト")
