import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import json
import os

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))  # paste your channel ID in the Render dashboard later

SEARCH_URL = 'https://www.davidjones.com/search?searchTerm=pokemon'
HEADERS = {'User-Agent': 'Mozilla/5.0'}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

def fetch_products():
    response = requests.get(SEARCH_URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    items = soup.select('[data-product-id]')

    products = {}
    for item in items:
        title = item.get('data-product-name')
        link = item.get('data-product-url')
        stock = item.get('data-product-instock') or "unknown"
        img_tag = item.select_one('img')
        image_url = img_tag['src'] if img_tag and 'src' in img_tag.attrs else None

        if title and link:
            products[title] = {
                'link': f"https://www.davidjones.com{link}",
                'stock': stock,
                'image': image_url
            }
    return products

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
    print(f"Logged in as {bot.user}")
    check_new_products.start()

@bot.command(name="search")
async def search(ctx):
    products = fetch_products()
    if not products:
        await ctx.send("❌ No Pokémon products found.")
        return

    for title, data in products.items():
        embed = discord.Embed(title=title, url=data['link'])
        embed.add_field(name="Stock", value=data['stock'])
        if data['image']:
            embed.set_thumbnail(url=data['image'])
        await ctx.send(embed=embed)

@tasks.loop(minutes=5)
async def check_new_products():
    products = fetch_products()
    previous = load_previous()
    new_items = {title: data for title, data in products.items() if title not in previous}

    if new_items:
        channel = bot.get_channel(CHANNEL_ID)
        for title, data in new_items.items():
            embed = discord.Embed(
                title=f"🧸 New Pokémon product: {title}",
                url=data['link'],
                description=f"📦 Stock: {data['stock']}"
            )
            if data['image']:
                embed.set_thumbnail(url=data['image'])

            msg = await channel.send(embed=embed)
            await msg.add_reaction("❤️")
            await msg.add_reaction("🛒")

        save_products(products)

bot.run(TOKEN)