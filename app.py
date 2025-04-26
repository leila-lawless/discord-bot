import os
import aiohttp
from flask import Flask
from threading import Thread
from dotenv import load_dotenv
import discord

# Web server setup
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Sentiment Bot is Alive!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

Thread(target=run_flask).start()

# Your bot code
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
MODEL_URL = os.getenv("MODEL_URL")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Bot is online as {client.user}")

@client.event
async def on_message(message):
    # ... keep your existing on_message code exactly as-is ...
    if message.channel.id != CHANNEL_ID or message.author == client.user:
        return

    user_text = message.content.strip()[:500]
    if not user_text:
        return

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                MODEL_URL,
                json={"text": user_text},
                headers={"Content-Type": "application/json"},
                timeout=15
            ) as res:
                
                print(f"API Status: {res.status}")  # Debug
                data = await res.json(content_type=None)
                print(f"Raw API Response: {data}")  # Debug
                
                # Handle numerical response (1/0)
                raw_sentiment = data.get("sentiment", 1)
                sentiment = "positive" if int(raw_sentiment) == 1 else "negative"

    except Exception as e:
        print(f"API Error: {str(e)}")
        sentiment = "neutral"

    # Responses with CORRECT KEYS
    responses = {
        "positive": "🌟 That's wonderful! What else made you feel this way?",
        "negative": "💔 I'm sorry to hear that. Would you like to share more?",
        "neutral": "🤔 Interesting perspective! Could you elaborate?"
    }
    
    reply = responses.get(sentiment, "🎈 Thanks for sharing! What's next?")

    async with message.channel.typing():
        await message.channel.send(reply)

client.run(TOKEN)
