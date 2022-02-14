import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

import KeepAlive
from MusicPlayer import MusicPlayer

intents = discord.Intents.default()
intents.members = True
intents.messages = True
activity = discord.Activity(type=discord.ActivityType.listening, name="for #help")
bot = commands.Bot(command_prefix='#', intents=intents, activity=activity)


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')


if __name__ == '__main__':
    bot.add_cog(MusicPlayer(bot))
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    KeepAlive.keep_alive()
    bot.run(TOKEN)
