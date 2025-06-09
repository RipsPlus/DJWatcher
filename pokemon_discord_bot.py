import os
import discord
from discord.ext import commands
import requests

# Environment variables
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

# Discord intents and setup
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

API_URL = "https://www.davidjones.com/api/catalogue/search?category=brand&brand=pokemon&rows=100&start=0"

def fetch_pokemon_products():
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        products = data.get("products", [])
        return products
    except Exception as e:
        print(f"Error fetching products: {e}")
        return []

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.command(name="check")
async def check_products(ctx):
    await ctx.send("🔎 Checking David Jones Pokémon products...")

    products = fetch_pokemon_products()

    if not products:
        await ctx.send("❌ No Pokémon products found.")
        return

    messages = []
    for p in products:
        name = p.get("productName", "Unnamed")
        price = p.get("salePrice", "N/A")
        url = "https://www.davidjones.com" + p.get("productUrl", "")
        messages.append(f"**{name}** - ${price}\n<{url}>")

    for msg in messages:
        await ctx.send(msg)

# Run the bot
bot.run(TOKEN)
