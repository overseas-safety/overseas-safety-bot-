import os
from atproto import Client, client_utils, models
from dotenv import load_dotenv

load_dotenv()

def main():
    handle = os.getenv("BLUESKY_HANDLE")
    password = os.getenv("BLUESKY_PASSWORD")
    
    client = Client()
    client.login(handle, password)
    
    builder1 = client_utils.TextBuilder()
    builder1.text("Test Post")
    post = client.send_post(builder1)
    
    root_ref = models.ComAtprotoRepoStrongRef.Main(cid=post.cid, uri=post.uri)
    reply_ref = models.AppBskyFeedPost.ReplyRef(parent=root_ref, root=root_ref)
    
    builder2 = client_utils.TextBuilder()
    builder2.text("Test Reply")
    reply = client.send_post(builder2, reply_to=reply_ref)
    print("Replied successfully")

if __name__ == "__main__":
    main()
