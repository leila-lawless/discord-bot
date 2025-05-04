import os
import aiohttp
from flask import Flask
from threading import Thread
from dotenv import load_dotenv
import discord
import random

# Web server
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Emotion Bot is Alive!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

Thread(target=run_flask).start()

# Discord bot setup
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
MODEL_URL = os.getenv("MODEL_URL")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Emotion-based responses
emotion_responses = {
    "joy": ["That's awesome! 😄", "Yay! I'm happy for you! 🎉", "You sound joyful! 😊"],
    "sadness": ["I'm here for you. 💙", "I'm sorry you're feeling down. 😢", "Sending hugs. 🤗"],
    "anger": ["Take a deep breath... 😤", "I'm sorry something made you angry. 💢", "Want to talk about it?"],
    "love": ["Aww, that's sweet! 💖", "Love is in the air! 💕", "That's heartwarming! 🥰"],
    "fear": ["It's okay to be scared. 🫂", "You’re not alone. 👻", "Want to talk about what’s worrying you?"],
    "surprise": ["Whoa! Didn’t expect that! 😲", "That's surprising! 😮", "Tell me more! 🤯"],
    "neutral": ["I see. 😊", "Hmm, tell me more.", "Interesting!"]
}

# Optional: Track user interactions
user_states = {}

@client.event
async def on_ready():
    print(f"Bot is online as {client.user}")
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("Hello everyone! I'm here to chat and listen to your feelings. 💬")

@client.event
async def on_message(message):
    if message.channel.id != CHANNEL_ID or message.author == client.user:
        return

    user_id = str(message.author.id)
    user_text = message.content.strip()[:500]
    if not user_text:
        return

    # Respond to greetings
    greetings = ["hi", "hello", "hey", "yo", "sup"]
    if user_text.lower() in greetings:
        await message.channel.send(random.choice([
            f"Hey {message.author.name}! How was your day? 😊",
            f"Hello {message.author.name}, feeling good today?",
            f"Hiya! Wanna talk about something?"
        ]))
        user_states[user_id] = "awaiting_day_response"
        return

    # Respond to follow-up after asking how was your day
    if user_states.get(user_id) == "awaiting_day_response":
        emotion = await get_emotion(user_text)
        reply = random.choice(emotion_responses.get(emotion, emotion_responses["neutral"]))
        await message.channel.send(reply)
        user_states[user_id] = None  # Reset state
        return

    # General emotion detection
    emotion = await get_emotion(user_text)
    reply = random.choice(emotion_responses.get(emotion, emotion_responses["neutral"]))
    await message.channel.send(reply)

# Helper function to call model
async def get_emotion(text):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                MODEL_URL,
                json={"text": text},
                headers={"Content-Type": "application/json"},
                timeout=15
            ) as res:
                print(f"API Status: {res.status}")
                data = await res.json(content_type=None)
                print(f"API Response: {data}")
                emotion = data.get("emotion", "neutral").lower()
                return emotion
    except Exception as e:
        print(f"API Error: {str(e)}")
        return "neutral"

client.run(TOKEN)
