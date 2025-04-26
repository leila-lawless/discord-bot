import os
from flask import Flask
from threading import Thread
import discord

# Web server to keep alive
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

Thread(target=run).start()

# Discord bot code
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.channel.id == CHANNEL_ID and message.author != client.user:
        await message.channel.send("Hello! 👋")

client.run(TOKEN)
