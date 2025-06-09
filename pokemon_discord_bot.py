import os
import discord
import requests
from bs4 import BeautifulSoup
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def fetch_pokemon_products():
    url = "https://www.davidjones.com/brand/pokemon?q=pokemon&redirect=1&search_category=search_suggestions"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch page. Status code: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # Debug output
    print("HTML received:\n", soup.prettify()[:5000])
    products = soup.select(".product-tile")
    print(f"Found {len(products)} product tiles")

    items = []
    for product in products:
        name = product.select_one(".product-name")
        price = product.select_one(".price")
        link = product.select_one("a")
        if name and link:
            items.append({
                "name": name.text.strip(),
                "price": price.text.strip() if price else "Price not found",
                "link": "https://www.davidjones.com" + link['href']
            })

    return items

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

@bot.command(name="check")
async def check_products(ctx):
    await ctx.send("🔍 Checking for Pokémon products...")
    products = fetch_pokemon_products()

    if not products:
        await ctx.send("⚠️ No Pokémon products found.")
        return

    for product in products:
        message = f"**{product['name']}**\nPrice: {product['price']}\nLink: {product['link']}"
        await ctx.send(message)

bot.run(TOKEN)
