import os
import aiohttp
import discord
import random
import asyncio
from dotenv import load_dotenv
from discord.ext import tasks

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
MODEL_URL = os.getenv("MODEL_URL")

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Global session handler
client_session = None
session_lock = asyncio.Lock()

# Emotion-based responses (unchanged)
emotion_responses = {
    "joy": ["That's awesome! 😄", "Yay! I'm happy for you! 🎉", "You sound joyful! 😊"],
    "sadness": ["I'm here for you. 💙", "I'm sorry you're feeling down. 😢", "Sending hugs. 🤗"],
    "anger": ["Take a deep breath... 😤", "I'm sorry something made you angry. 💢", "Want to talk about it?"],
    "love": ["Aww, that's sweet! 💖", "Love is in the air! 💕", "That's heartwarming! 🥰"],
    "fear": ["It's okay to be scared. 🫂", "You’re not alone. 👻", "Want to talk about what’s worrying you?"],
    "surprise": ["Whoa! Didn’t expect that! 😲", "That's surprising! 😮", "Tell me more! 🤯"],
    "neutral": ["I see. 😊", "Hmm, tell me more.", "Interesting!"]
}

# Track user conversation state
user_states = {}

@tasks.loop(minutes=15)
async def clean_states():
    user_states.clear()

async def create_session():
    global client_session
    async with session_lock:
        if client_session is None or client_session.closed:
            client_session = aiohttp.ClientSession()

@client.event
async def on_ready():
    print(f"Bot is online as {client.user}")
    await create_session()
    clean_states.start()
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("Hello everyone! I'm here to chat and listen to your feelings. 💬")

@client.event
async def on_disconnect():
    if client_session and not client_session.closed:
        await client_session.close()

@client.event
async def on_message(message):
    if message.author.bot or message.channel.id != CHANNEL_ID:
        return

    user_id = str(message.author.id)
    user_text = message.content.strip()[:500]
    
    if not user_text:
        return

    # Respond to greetings (unchanged)
    greetings = ["hi", "hello", "hey", "yo", "sup"]
    if user_text.lower() in greetings:
        async with message.channel.typing():
            await message.channel.send(random.choice([
                f"Hey {message.author.name}! How was your day? 😊",
                f"Hello {message.author.name}, feeling good today?",
                f"Hiya! Wanna talk about something?"
            ]))
        user_states[user_id] = "awaiting_day_response"
        return

    # Response handling (unchanged)
    async with message.channel.typing():
        if user_states.get(user_id) == "awaiting_day_response":
            emotion = await get_emotion(user_text)
            reply = random.choice(emotion_responses.get(emotion, emotion_responses["neutral"]))
            await message.channel.send(reply)
            user_states[user_id] = None
        else:
            emotion = await get_emotion(user_text)
            reply = random.choice(emotion_responses.get(emotion, emotion_responses["neutral"]))
            await message.channel.send(reply)

async def get_emotion(text):
    retries = 3
    for attempt in range(retries):
        try:
            if not client_session or client_session.closed:
                await create_session()
                
            async with client_session.post(
                MODEL_URL,
                json={"text": text},
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as res:
                if res.status != 200:
                    print(f"API Error: Status {res.status}")
                    continue
                
                content_type = res.headers.get('Content-Type', '')
                if 'application/json' not in content_type:
                    print("API Error: Non-JSON response")
                    continue
                
                data = await res.json()
                return data.get("sentiment", "neutral").lower()
        
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < retries - 1:
                await asyncio.sleep(1 * (attempt + 1))
                continue
            return "neutral"
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return "neutral"

client.run(TOKEN)
