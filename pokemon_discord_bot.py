import os
import discord
import requests
from bs4 import BeautifulSoup
from discord.ext import commands

# Retrieve environment variables directly
TOKEN = os.environ.get("DISCORD_TOKEN")
CHANNEL_ID = int(os.environ.get("DISCORD_CHANNEL_ID"))

# Set up Discord bot with appropriate intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def fetch_pokemon_products():
    url = "https://www.davidjones.com/brand/pokemon"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch page. Status code: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # Find all product containers
    products = soup.find_all("div", class_="product-tile")

    items = []
    for product in products:
        # Extract product name
        name_tag = product.find("div", class_="product-name")
        name = name_tag.get_text(strip=True) if name_tag else "No name found"

        # Extract product price
        price_tag = product.find("span", class_="price")
        price = price_tag.get_text(strip=True) if price_tag else "Price not found"

        # Extract product link
        link_tag = product.find("a", href=True)
        link = "https://www.davidjones.com" + link_tag['href'] if link_tag else "No link found"

        items.append(f"{name} - {price}\n{link}")

    return items

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def check(ctx):
    await ctx.send("Checking for Pokémon products at David Jones...")
    products = fetch_pokemon_products()
    if products:
        for item in products:
            await ctx.send(item)
    else:
        await ctx.send("No Pokémon products found at David Jones.")

bot.run(TOKEN)
