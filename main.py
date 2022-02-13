import os
from dotenv import load_dotenv

import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True
intents.messages = True
activity = discord.Activity(type=discord.ActivityType.listening, name="for #help")
bot = commands.Bot(command_prefix='#', intents=intents, activity=activity)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

if __name__ == '__main__':
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    bot.run(TOKEN)