import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
ROLE_ID = os.getenv("DISCORD_ROLE_ID")  # Optional

SEARCH_URL = 'https://www.davidjones.com/brand/pokemon?q=pokemon&redirect=1&search_category=search_suggestions'
HEADERS = {'User-Agent': 'Mozilla/5.0'}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

def fetch_products():
    try:
        response = requests.get(SEARCH_URL, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.select('[data-product-id]')
        products = {}
        debug_info = []

        for item in items:
            title = item.get('data-product-name')
            link = item.get('data-product-url')
            stock = item.get('data-product-instock') or "unknown"
            img_tag = item.select_one('img')
            image_url = img_tag['src'] if img_tag and 'src' in img_tag.attrs else None
            visibility = "visible" if title and link else "possibly hidden or incomplete"

            if title:
                products[title] = {
                    'link': f"https://www.davidjones.com{link}" if link else "unknown",
                    'stock': stock,
                    'image': image_url,
                    'visibility': visibility
                }
                debug_info.append(f"{title} — Stock: {stock} — Visibility: {visibility}")
        return products, debug_info
    except Exception as e:
        return {}, [f"⚠️ Error during fetch: {str(e)}"]

def load_previous():
    try:
        with open("pokemon_products.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_products(products):
    with open("pokemon_products.json", "w") as f:
        json.dump(products, f)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    check_products.start()
    daily_summary.start()

@bot.command(name="check")
async def manual_check(ctx):
    products, debug_info = fetch_products()
    if not products:
        await ctx.send("❌ No Pokémon products found.")
        return

    for title, data in products.items():
        embed = discord.Embed(title=title, url=data['link'])
        embed.add_field(name="Stock", value=data['stock'])
        if data['image']:
            embed.set_thumbnail(url=data['image'])
        await ctx.send(embed=embed)

    debug_message = "**🔍 Debug Info:**
" + "\n".join(debug_info)
    await ctx.send(debug_message[:1999])

@tasks.loop(seconds=90)
async def check_products():
    products, debug_info = fetch_products()
    previous = load_previous()

    new_items = {title: data for title, data in products.items() if title not in previous}
    out_of_stock_items = {
        title: data for title, data in previous.items()
        if title in products and data['stock'].lower() != "out of stock"
        and products[title]['stock'].lower() == "out of stock"
    }
    back_in_stock_items = {
        title: data for title, data in products.items()
        if title in previous and previous[title]['stock'].lower() == "out of stock"
        and data['stock'].lower() != "out of stock"
    }
    removed_items = {title: data for title in previous if title not in products}

    if new_items or out_of_stock_items or removed_items or back_in_stock_items:
        channel = bot.get_channel(CHANNEL_ID)

        for title, data in new_items.items():
            embed = discord.Embed(
                title=f"🆕 New Pokémon product: {title}",
                url=data['link'],
                description=f"📦 Stock: {data['stock']}"
            )
            if data['image']:
                embed.set_thumbnail(url=data['image'])
            msg = await channel.send(content=f"<@&{ROLE_ID}>" if ROLE_ID else None, embed=embed)
            await msg.add_reaction("❤️")
            await msg.add_reaction("🛒")

        for title, data in out_of_stock_items.items():
            embed = discord.Embed(
                title=f"📭 Out of Stock: {title}",
                url=data['link'],
                description="This item is now out of stock."
            )
            if data['image']:
                embed.set_thumbnail(url=data['image'])
            await channel.send(embed=embed)

        for title, data in back_in_stock_items.items():
            embed = discord.Embed(
                title=f"📦 Back in Stock: {title}",
                url=data['link'],
                description="This item is available again!"
            )
            if data['image']:
                embed.set_thumbnail(url=data['image'])
            await channel.send(embed=embed)

        for title, data in removed_items.items():
            embed = discord.Embed(
                title=f"🚫 Removed from Store: {title}",
                url=data['link'],
                description="This product is no longer listed."
            )
            if data['image']:
                embed.set_thumbnail(url=data['image'])
            await channel.send(embed=embed)

        save_products(products)

@tasks.loop(minutes=1)
async def daily_summary():
    now = datetime.now().time()
    if now.hour == 20 and now.minute == 0:
        products, _ = fetch_products()
        if products:
            channel = bot.get_channel(CHANNEL_ID)
            await channel.send("🗓️ **Daily Pokémon Product Summary:**")
            for title, data in products.items():
                embed = discord.Embed(title=title, url=data['link'])
                embed.add_field(name="Stock", value=data['stock'])
                if data['image']:
                    embed.set_thumbnail(url=data['image'])
                await channel.send(embed=embed)

bot.run(TOKEN)