import os
import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")

@bot.command()
async def check(ctx):
    if ctx.channel.id != CHANNEL_ID:
        return

    url = "https://www.davidjones.com/brand/pokemon?q=pokemon&redirect=1&search_category=search_suggestions"
    headers = {
        "User-Agent": "Mozilla/5.0",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        await ctx.send(f"❌ Failed to fetch data: {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    product_elements = soup.select(".product-tile__details")

    if not product_elements:
        await ctx.send("😕 No Pokémon products found.")
        return

    messages = []
    for product in product_elements:
        name_tag = product.select_one(".product-tile__name")
        price_tag = product.select_one(".product-tile__price-value")
        link_tag = product.find_parent("a")

        name = name_tag.get_text(strip=True) if name_tag else "No name"
        price = price_tag.get_text(strip=True) if price_tag else "No price"
        link = "https://www.davidjones.com" + link_tag["href"] if link_tag else "No link"

        messages.append(f"**{name}** - {price}\n{link}")

    await ctx.send("\n\n".join(messages[:10]))  # Discord message limit
    if len(messages) > 10:
        await ctx.send(f"...and {len(messages) - 10} more items.")

bot.run(TOKEN)
