import os
import time
import aiohttp
from dotenv import load_dotenv
import discord

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
    # Prevent self-responses
    if message.author == client.user:
        return
    
    # Only allow specific channel
    if message.channel.id != CHANNEL_ID:
        return
    
    # Cooldown check
    cooldown = 5  # Seconds between responses
    if hasattr(client, "last_response") and (time.time() - client.last_response) < cooldown:
        return
    client.last_response = time.time()

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
                data = await res.json(content_type=None)
                raw_sentiment = data.get("sentiment", 1)
                sentiment = "positive" if int(raw_sentiment) == 1 else "negative"

    except Exception as e:
        print(f"API Error: {str(e)}")
        sentiment = "neutral"

    responses = {
        "positive": "That's wonderful! ☺️🌟",
        "negative": "I'm sorry to hear that 😢💔",
    }
    
    reply = responses.get(sentiment, "What happened? 🤔")

    async with message.channel.typing():
        await message.channel.send(reply)

client.run(TOKEN)
