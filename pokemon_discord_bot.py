import os
import requests
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def fetch_pokemon_products():
    try:
        response = requests.get(
            "https://www.davidjones.com/api/catalogue/search?category=brand&brand=pokemon&rows=100&start=0",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("products", [])
        else:
            print(f"Error: Received status code {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception during fetch: {e}")
        return None

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user.name}")

@bot.command(name="check")
async def check_products(ctx):
    await ctx.send("🔎 Checking David Jones Pokémon products...")

    products = fetch_pokemon_products()

    if products is None:
        await ctx.send("⚠️ Failed to fetch data from API.")
        return

    await ctx.send(f"🔢 Products fetched from API: {len(products)}")

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

bot.run(TOKEN)
