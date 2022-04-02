import discord
import asyncio
from youtube_dl import YoutubeDL
from discord import FFmpegPCMAudio
from discord.utils import get
from discord.ext import commands


class MusicPlayer(commands.Cog,
                  name="Music",
                  description="Commands to play music from YouTube and other music streaming services"):

    def __init__(self, bot):
        self.bot = bot

    loop = asyncio.get_event_loop()
    song_queue = []
    current_song = None
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
            'preferredquality': '140',
        }],
        'default_search': 'auto',
        'source_address': '0.0.0.0'
    }

    @commands.command(help='Tells the bot to join the voice channel')
    async def join(self, ctx, from_play=False):

        bot_voice = ctx.message.guild.voice_client
        sender_voice = ctx.message.author.voice
        if not sender_voice:
            await ctx.message.add_reaction('❓')
            await ctx.send("You are not connected to a voice channel")
            return

        if not bot_voice:
            await ctx.message.add_reaction('👋')
            await sender_voice.channel.connect()
            m = ctx.guild.get_member(self.bot.user.id)
            await m.edit(deafen=True)
        else:
            if bot_voice.channel != sender_voice.channel:
                await ctx.message.add_reaction('❓')
                await ctx.send("Sorry, I'm already in another voice channel")
                return
            elif not from_play:
                await ctx.message.add_reaction('❓')
                await ctx.send("I'm here, you can't make me come second time")

    @commands.command(help='Tells the bot to leave the voice channel')
    async def leave(self, ctx):
        bot_voice = ctx.message.guild.voice_client
        sender_voice = ctx.message.author.voice
        if not sender_voice:
            await ctx.message.add_reaction('❓')
            await ctx.send("You are not connected to a voice channel")
            return

        if not bot_voice:
            await ctx.message.add_reaction('❓')
            await ctx.send("I'm not in a voice channel.")
            return
        else:
            if bot_voice.channel != sender_voice.channel:
                await ctx.message.add_reaction('❓')
                await ctx.send("I'm in a different channel, you can't make me leave")
                return
            else:
                await ctx.message.add_reaction('👋')
                self.current_song = None
                await bot_voice.disconnect()

    @commands.command(help='To play a song', aliases=['p'])
    async def play(self, ctx, *, arg):
        await self.join(ctx, True)
        voice = get(self.bot.voice_clients, guild=ctx.guild)

        async with ctx.typing():
            await ctx.message.add_reaction('▶')
            song = await self.search_yt(str(arg))
            self.song_queue.append(song)

            if not voice.is_playing():
                await self.run_a_song(ctx)
            else:
                embed = discord.Embed()
                embed.title = "Added to queue: "
                embed.description = "[" + song['title'] + "](" + song['webpage_url'] + ")"
                asyncio.run_coroutine_threadsafe(ctx.send(embed=embed), self.bot.loop)

    @commands.command(help='To skip to next song', aliases=['s'])
    async def skip(self, ctx):
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        if voice is not None:
            if voice.is_playing():
                await ctx.message.add_reaction('⏭')
                voice.stop()
            else:
                await ctx.message.add_reaction('❓')
                await ctx.send("I'm not playing anything right now")
        else:
            await ctx.message.add_reaction('❓')
            await ctx.send("I'm not even in voice channel, what do you expect me to do?")

    async def run_a_song(self, ctx):
        voice = get(self.bot.voice_clients, guild=ctx.guild)

        if len(self.song_queue) >= 1:
            song = self.song_queue.pop(0)
            self.current_song = song
            voice.play(FFmpegPCMAudio(source=song['url'], executable='ffmpeg',
                                      before_options=['--enable-demuxer=mov', '-reconnect 1', '-reconnect_streamed 1',
                                                      '-reconnect_delay_max 5'],
                                      options=['-vn', '-sn', '-dn', '-ignore_unknown']),
                       after=lambda ex: asyncio.run_coroutine_threadsafe(self.run_a_song(ctx), self.bot.loop))

            embed = discord.Embed()
            embed.title = "Now playing: "
            embed.description = "[" + song['title'] + "](" + song['webpage_url'] + ")"
            embed.set_image(url=song['thumbnail'])
            asyncio.run_coroutine_threadsafe(ctx.send(embed=embed), self.bot.loop)
        else:
            self.current_song = None
            asyncio.run_coroutine_threadsafe(ctx.send("Nothing else left to play!"), self.bot.loop)

    async def search_yt(self, arg):
        with YoutubeDL(self.ydl_opts) as ydl:
            if arg[0:4] == "http":
                video = ydl.extract_info(arg, download=False)
            else:
                video = ydl.extract_info(f"ytsearch:{arg}", download=False)['entries'][0]
        return video

    @commands.command(help='Stops the song and clears the queue')
    async def stop(self, ctx):
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        if voice is not None:
            if voice.is_playing():
                self.song_queue.clear()
                self.current_song = None
                await ctx.message.add_reaction('⏹')
                voice.stop()
            else:
                await ctx.message.add_reaction('❓')
                await ctx.send("I'm not playing anything right now")
        else:
            await ctx.message.add_reaction('❓')
            await ctx.send("I'm not even in voice channel, what do you expect me to do?")

    @commands.command(help='Removes song from queue', aliases=['rm'])
    async def remove(self, ctx, index):
        if len(self.song_queue) == 0:
            await ctx.message.add_reaction('❓')
            await ctx.send("There is nothing to remove")
        elif int(index) > len(self.song_queue):
            await ctx.message.add_reaction('❓')
            await ctx.send("There's no song with that number in the queue")
        else:
            self.song_queue.pop(int(index) - 1)
            await ctx.message.add_reaction('❌')

    @commands.command(aliases=['q'], help='Shows content of the music queue')
    async def queue(self, ctx):
        if len(self.song_queue) == 0 and not self.current_song:
            await ctx.send("The queue is empty!")
            await ctx.message.add_reaction('❓')
            return
        elif self.current_song:
            embed = discord.Embed()
            now = "[" + self.current_song['title'] + "](" + self.current_song['webpage_url'] + ")"
            embed.add_field(name="Now playing:", value=now, inline=False)
            i = 1
            songs = ""
            for song in self.song_queue:
                songs += str(i) + ". [" + song['title'] + "](" + song['webpage_url'] + ")\n"
                i += 1
            if songs != "":
                embed.add_field(name="Coming next:", value=songs, inline=False)
            await ctx.send(embed=embed)
            await ctx.message.add_reaction('🇶')