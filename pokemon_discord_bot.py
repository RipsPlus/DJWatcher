import os
import asyncio
import discord
from discord.ext import commands, tasks
import requests

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Store known products for tracking new/out-of-stock/removed
known_products = {}

API_URL = "https://www.davidjones.com/api/catalogue/search?category=brand&brand=pokemon&rows=100&start=0"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.davidjones.com/brand/pokemon",
    "Origin": "https://www.davidjones.com",
}

def fetch_products():
    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error fetching products: {e}")
        return {}

    products = {}
    items = data.get("items", [])

    for item in items:
        name = item.get("name")
        url_path = item.get("urlPath")
        full_url = "https://www.davidjones.com" + url_path if url_path else None
        image = None
        images = item.get("images", [])
        if images:
            image = images[0].get("url")
        availability = item.get("stockAvailability", "Unknown")
        visibility = item.get("visibility", "Unknown")

        if full_url and name:
            products[full_url] = {
                "name": name,
                "url": full_url,
                "image": image,
                "availability": availability,
                "visibility": visibility,
            }
    return products

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")
    product_scan.start()

@tasks.loop(seconds=90)
async def product_scan():
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print(f"Channel ID {CHANNEL_ID} not found!")
        return

    current_products = fetch_products()
    if not current_products:
        print("No products fetched during scan.")
        return

    global known_products

    # Check for new products
    for url, info in current_products.items():
        if url not in known_products:
            # New product found
            msg = f"🆕 **New Pokémon product listed!**\n**{info['name']}**\nAvailability: {info['availability']}\nVisibility: {info['visibility']}\n{info['url']}"
            embed = discord.Embed(title=info['name'], url=info['url'], description=f"Availability: {info['availability']}\nVisibility: {info['visibility']}")
            if info['image']:
                embed.set_thumbnail(url=info['image'])
            await channel.send(msg, embed=embed)

        else:
            # Existing product: check for stock changes
            old_avail = known_products[url].get("availability")
            new_avail = info['availability']
            if old_avail != new_avail:
                msg = f"⚠️ **Stock change for:** {info['name']}\nOld: {old_avail}\nNew: {new_avail}\n{info['url']}"
                embed = discord.Embed(title=info['name'], url=info['url'], description=f"Availability changed from **{old_avail}** to **{new_avail}**")
                if info['image']:
                    embed.set_thumbnail(url=info['image'])
                await channel.send(msg, embed=embed)

            # Check visibility changes (optional)
            old_vis = known_products[url].get("visibility")
            new_vis = info['visibility']
            if old_vis != new_vis:
                msg = f"👁️ **Visibility changed for:** {info['name']}\nOld: {old_vis}\nNew: {new_vis}\n{info['url']}"
                embed = discord.Embed(title=info['name'], url=info['url'], description=f"Visibility changed from **{old_vis}** to **{new_vis}**")
                if info['image']:
                    embed.set_thumbnail(url=info['image'])
                await channel.send(msg, embed=embed)

    # Check for removed products
    removed_urls = set(known_products.keys()) - set(current_products.keys())
    for url in removed_urls:
        info = known_products[url]
        msg = f"❌ **Product removed:** {info['name']}\nLast known availability: {info['availability']}\n{url}"
        embed = discord.Embed(title=info['name'], description=f"Product was removed from listing.", url=url)
        if info['image']:
            embed.set_thumbnail(url=info['image'])
        await channel.send(msg, embed=embed)

    known_products = current_products.copy()

@bot.command(name="check")
async def manual_check(ctx):
    current_products = fetch_products()
    if not current_products:
        await ctx.send("No Pokémon products found right now.")
        return

    lines = []
    for info in current_products.values():
        line = f"**{info['name']}**\nAvailability: {info['availability']}\nVisibility: {info['visibility']}\n{info['url']}\n"
        lines.append(line)

    message = "\n".join(lines)
    # Discord message limit is 2000 characters, so we chunk if needed
    for chunk_start in range(0, len(message), 1900):
        await ctx.send(message[chunk_start:chunk_start+1900])

if __name__ == "__main__":
    bot.run(TOKEN)
