import os
import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

PRODUCTS_URL = "https://www.davidjones.com/brand/pokemon?q=pokemon&redirect=1&search_category=search_suggestions"

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.command(name="check")
async def check_products(ctx):
    if ctx.channel.id != CHANNEL_ID:
        return

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(PRODUCTS_URL, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    items = soup.find_all("a", class_="product-tile")

    if not items:
        await ctx.send("❌ No Pokémon products found.")
        return

    message_lines = ["**🎯 Current Pokémon Products:**\n"]

    for item in items:
        name = item.get("title", "Unnamed Product")
        link = "https://www.davidjones.com" + item.get("href", "")
        message_lines.append(f"- [{name}]({link})")

    await ctx.send("\n".join(message_lines)[:1999])

bot.run(TOKEN)
