import os
import requests
import subprocess
import urllib.parse
from google import genai
import feedparser
from dotenv import load_dotenv

load_dotenv()

def get_latest_news():
    url = "http://feeds.bbci.co.uk/news/world/rss.xml"
    feed = feedparser.parse(url)
    if feed.entries:
        return feed.entries[0].title
    return "Global tensions rise as geopolitical shifts continue."

def generate_script(news_headline):
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
Write a short, engaging 4-sentence TikTok/Shorts script in English.
Topic: A breaking news headline followed by a practical safety tip for travelers or businesses.
Headline: {news_headline}

Rules:
- No emojis, no hashtags, no markdown.
- Plain text only.
- Sentence 1: Catchy hook summarizing the news.
- Sentence 2: The severe risk or geopolitical impact.
- Sentence 3: A practical, actionable security tip (e.g., situational awareness, digital security, emergency planning).
- Sentence 4: "Stay safe and check the link in our bio for complete security guides."
"""
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    return response.text.replace('\n', ' ').replace('**', '').replace('*', '').strip()

def create_video():
    news = get_latest_news()
    print(f"Latest news: {news}")
    
    script = generate_script(news)
    print(f"Generated Script: {script}")
    
    print("Generating Audio and Subtitles with AI Voice...")
    # Generate MP3 and VTT using edge-tts (native Microsoft Azure Neural Voices)
    subprocess.run([
        "edge-tts", 
        "--text", script, 
        "--voice", "en-US-ChristopherNeural", 
        "--rate", "+10%", 
        "--write-media", "audio.mp3", 
        "--write-subtitles", "subs.vtt"
    ], check=True)
    
    print("Downloading Background Image from Pollinations AI...")
    img_prompt = urllib.parse.quote("A dramatic stylized world map background, cyber security interface, cinematic lighting, highly detailed, vertical aspect ratio 9:16")
    img_url = f"https://image.pollinations.ai/prompt/{img_prompt}?width=1080&height=1920&nologo=true"
    r = requests.get(img_url)
    with open("bg.jpg", "wb") as f:
        f.write(r.content)
        
    print("Synthesizing Video with FFmpeg (Zoom effect + Subtitles)...")
    # FFmpeg command to combine image with zoompan, audio, and subtitles
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", "bg.jpg",
        "-i", "audio.mp3",
        "-vf", "zoompan=z='min(zoom+0.001,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1500:s=1080x1920,subtitles=subs.vtt:force_style='FontSize=22,Alignment=2,PrimaryColour=&H00FFFF,OutlineColour=&H40000000,BorderStyle=3,MarginV=60'",
        "-c:v", "libx264",
        "-preset", "fast",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        "output.mp4"
    ]
    subprocess.run(ffmpeg_cmd, check=True)
    print("✅ Video generation complete!")

def send_to_telegram():
    print("Sending MP4 to Telegram...")
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("Telegram credentials missing.")
        return
        
    url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
    caption = (
        "🎬 **Your Automated Short Video is Ready!** 🎬\n\n"
        "Download this MP4 and upload it directly to **YouTube Shorts** and **TikTok**.\n"
        "The AI has already perfectly timed the subtitles, visuals, and native English voiceover.\n\n"
        "Title suggestion: `Global Security Alert 🚨 #Geopolitics #TravelSafety`\n"
        "Link in bio: `https://security-products.vercel.app/`"
    )
    
    with open("output.mp4", "rb") as video:
        files = {'video': video}
        data = {'chat_id': chat_id, 'caption': caption, 'parse_mode': 'Markdown'}
        r = requests.post(url, files=files, data=data)
        
    if r.status_code == 200:
        print("✅ Successfully sent video to Telegram!")
    else:
        print("❌ Failed to send video:", r.text)

if __name__ == "__main__":
    create_video()
    send_to_telegram()
