import os
import requests
from atproto import Client, models
from dotenv import load_dotenv

load_dotenv()

def update_telegram_profile():
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("Telegram bot token missing")
        return

    name = "Global Safety Alerts"
    description = "Real-time alerts, crisis updates, and geopolitical analysis. Stay ahead of global risks.\n\n🔒 Get our exclusively curated personal & business security resources via our official links below!"
    short_description = "Breaking news & global security alerts for travelers and businesses."

    try:
        res1 = requests.post(f"https://api.telegram.org/bot{bot_token}/setMyShortDescription", json={"short_description": short_description})
        res2 = requests.post(f"https://api.telegram.org/bot{bot_token}/setMyDescription", json={"description": description})
        res3 = requests.post(f"https://api.telegram.org/bot{bot_token}/setMyName", json={"name": name})
        print("Telegram updated successfully!")
    except Exception as e:
        print("Failed to update Telegram profile:", e)


def update_bluesky_profile():
    handle = os.getenv("BLUESKY_HANDLE")
    password = os.getenv("BLUESKY_PASSWORD")
    if not handle or not password:
        print("Bluesky credentials missing")
        return

    client = Client()
    try:
        client.login(handle, password)
        
        # Fetch existing profile
        current_profile = client.app.bsky.actor.profile.get(client.me.did, 'self')
        
        if current_profile and current_profile.value:
            new_record = current_profile.value
        else:
            new_record = models.AppBskyActorProfile.Record()
            
        new_record.displayName = "Global Safety & Geopolitics Alerts"
        new_record.description = "AI-driven realtime alerts on global security, geopolitical risks, and travel safety. 🚨 Join our Telegram for breaking alerts. \n🔒 Security guides available."
        
        # Save record
        client.com.atproto.repo.put_record({
            'repo': client.me.did,
            'collection': 'app.bsky.actor.profile',
            'rkey': 'self',
            'record': new_record
        })
        print("Bluesky profile updated successfully!")
    except Exception as e:
        print("Failed to update Bluesky profile:", e)

if __name__ == "__main__":
    update_telegram_profile()
    update_bluesky_profile()
