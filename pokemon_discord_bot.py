import os
import discord
import asyncio
import requests
import json
from discord.ext import commands, tasks
from bs4 import BeautifulSoup
from datetime import datetime, time as dt_time

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
ROLE_ID = os.getenv("DISCORD_ROLE_ID")

URL = "https://www.davidjones.com/brand/pokemon"
HEADERS = {"User-Agent": "Mozilla/5.0"}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

previous_products = {}

def fetch_products():
    response = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")
    product_elements = soup.select(".product-tile")
    products = {}
    for element in product_elements:
        name_tag = element.select_one(".product-name")
        link_tag = element.select_one("a")
        image_tag = element.select_one("img")
        if name_tag and link_tag:
            name = name_tag.get_text(strip=True)
            url = "https://www.davidjones.com" + link_tag["href"]
            image = image_tag["src"] if image_tag else None
            products[url] = {"name": name, "url": url, "image": image}
    return products

def load_previous_products():
    if os.path.exists("pokemon_products.json"):
        with open("pokemon_products.json", "r") as f:
            return json.load(f)
    return {}

def save_previous_products(data):
    with open("pokemon_products.json", "w") as f:
        json.dump(data, f)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    global previous_products
    previous_products = load_previous_products()
    check_products.start()
    send_daily_report.start()

@bot.command(name="check")
async def check(ctx):
    products = fetch_products()
    if not products:
        await ctx.send("❌ No Pokémon products found.")
        return
    for p in products.values():
        embed = discord.Embed(title=p['name'], url=p['url'], color=0x00ff00)
        if p['image']:
            embed.set_thumbnail(url=p['image'])
        await ctx.send(embed=embed)

@tasks.loop(seconds=90)
async def check_products():
    global previous_products
    current = fetch_products()
    channel = bot.get_channel(CHANNEL_ID)

    new = {k: v for k, v in current.items() if k not in previous_products}
    removed = {k: v for k, v in previous_products.items() if k not in current}

    for url, prod in new.items():
        embed = discord.Embed(title=f"🆕 New Product: {prod['name']}", url=url, color=0x00ff00)
        if prod['image']:
            embed.set_thumbnail(url=prod['image'])
        if ROLE_ID:
            await channel.send(content=f"<@&{ROLE_ID}>", embed=embed)
        else:
            await channel.send(embed=embed)

    for url, prod in removed.items():
        embed = discord.Embed(title=f"❌ Removed: {prod['name']}", url=url, color=0xff0000)
        await channel.send(embed=embed)

    previous_products = current
    save_previous_products(previous_products)

@tasks.loop(time=dt_time(20, 0))
async def send_daily_report():
    channel = bot.get_channel(CHANNEL_ID)
    products = fetch_products()
    if not products:
        await channel.send("📊 Daily Report: No Pokémon products currently listed.")
        return
    embed = discord.Embed(title="📊 Daily Pokémon Product Report", color=0x0099ff)
    for i, p in enumerate(products.values()):
        embed.add_field(name=p['name'], value=f"[View Product]({p['url']})", inline=False)
        if i == 24:
            break
    await channel.send(embed=embed)

@bot.command(name="debug")
async def debug(ctx):
    debug_info = []
    debug_info.append(f"Total loaded products: {len(previous_products)}")
    debug_info.append(f"Latest keys: {list(previous_products.keys())[:3]}")
    debug_message = "**🔍 Debug Info:**\n" + "\n".join(debug_info)
    await ctx.send(debug_message[:1999])

bot.run(TOKEN)