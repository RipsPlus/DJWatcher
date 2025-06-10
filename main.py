import discord
import requests
import json
import os
from bs4 import BeautifulSoup
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command()
async def check(ctx):
    url = "https://www.davidjones.com/brand/pokemon?q=pokemon&redirect=1&search_category=search_suggestions"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    product_elements = soup.select("div.product-tile")

    if not product_elements:
        await ctx.send("No Pokémon products found.")
        return

    product_list = []
    for product in product_elements:
        name = product.select_one(".product-name").get_text(strip=True)
        link = "https://www.davidjones.com" + product.select_one("a")["href"]
        image = product.select_one("img")["src"]
        price = product.select_one(".product-sales-price, .product-standard-price")
        price_text = price.get_text(strip=True) if price else "Price not found"

        product_list.append({
            "name": name,
            "link": link,
            "image": image,
            "price": price_text
        })

    for item in product_list[:10]:
        embed = discord.Embed(title=item["name"], url=item["link"], description=item["price"])
        embed.set_thumbnail(url=item["image"])
        await ctx.send(embed=embed)

bot.run(os.getenv("DISCORD_TOKEN"))