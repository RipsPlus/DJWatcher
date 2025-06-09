import os
import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import json
import asyncio
from datetime import datetime, time, timedelta

# --- CONFIG ---
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
URL = "https://www.davidjones.com/brand/pokemon"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

CHECK_INTERVAL = 90  # seconds

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Store known products: key=product_url, value=dict with product info and availability
known_products = {}

def fetch_products():
    response = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    # Parse JSON-LD script containing product info
    scripts = soup.find_all("script", {"type": "application/ld+json"})
    products = {}

    for script in scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and data.get("@type") == "ItemList":
                for item in data.get("itemListElement", []):
                    product = item.get("item", {})
                    url = product.get("url")
                    name = product.get("name")
                    image = product.get("image")
                    if url and name:
                        full_url = url if url.startswith("http") else "https://www.davidjones.com" + url
                        products[full_url] = {
                            "name": name,
                            "url": full_url,
                            "image": image,
                            "availability": "Unknown"  # Placeholder: site doesn't expose exact stock in JSON-LD
                        }
        except Exception:
            continue

    return products

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")
    product_checker.start()

@tasks.loop(seconds=CHECK_INTERVAL)
async def product_checker():
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print(f"Channel ID {CHANNEL_ID} not found.")
        return

    try:
        current_products = fetch_products()

        # Check for new products
        new_products = {url: info for url, info in current_products.items() if url not in known_products}
        # Check for removed products
        removed_products = {url: info for url, info in known_products.items() if url not in current_products}

        # Send notifications for new products
        for url, info in new_products.items():
            embed = discord.Embed(title="🆕 New Pokémon Product Listed!", description=info["name"], url=url, color=0x00ff00)
            if info.get("image"):
                embed.set_thumbnail(url=info["image"])
            embed.add_field(name="Availability", value=info.get("availability", "Unknown"))
            await channel.send(embed=embed)
            known_products[url] = info

        # Send notifications for removed products
        for url, info in removed_products.items():
            embed = discord.Embed(title="❌ Pokémon Product Removed", description=info["name"], url=url, color=0xff0000)
            await channel.send(embed=embed)
            known_products.pop(url)

    except Exception as e:
        await channel.send(f"⚠️ Error during product check: {e}")

@bot.command(name="check")
async def manual_check(ctx):
    products = fetch_products()
    if not products:
        await ctx.send("No Pokémon products found at the moment.")
        return

    msg_lines = ["**Current Pokémon Products:**"]
    for info in products.values():
        line = f"- [{info['name']}]({info['url']})"
        msg_lines.append(line)

    # Update known_products with manual check results (optional)
    global known_products
    known_products = products

    # Discord message limit is 2000 chars
    message = "\n".join(msg_lines)
    await ctx.send(message[:1999])

@bot.command(name="debug")
async def debug(ctx):
    debug_info = [
        f"Bot User: {bot.user}",
        f"Channel ID: {CHANNEL_ID}",
        f"Known Products Count: {len(known_products)}",
        f"Check Interval: {CHECK_INTERVAL} seconds"
    ]
    debug_message = """**🔍 Debug Info:**\n""" + "\n".join(debug_info)
    await ctx.send(debug_message[:1999])

# Run the bot
bot.run(TOKEN)