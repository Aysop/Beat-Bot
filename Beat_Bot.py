import os
import discord
import youtube_dl
from discord.ext import commands
import asyncio


class bot:
    def __init__(self, counter=0):
        self._counter = counter

    # getter method
    def get_counter(self):
        return self._counter

    # setter method
    def set_counter(self, x):
        self._counter = x

    song_list = []
    command = False


loop = asyncio.get_event_loop()
client = commands.Bot(command_prefix=["!", "&", "-"])
beat_bot = bot()


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.command()
async def play(ctx, url: str):
    await asyncio.sleep(.5)
    song_there = os.path.isfile("song.mp3")
    try:
        if song_there:
            os.remove("song.mp3")
    except PermissionError:
        beat_bot.song_list.append(url)
        await ctx.send("Song added to queue")
        return

    voice_channel = ctx.author.voice.channel

    if ctx.voice_client is None:
        voice = await voice_channel.connect()
        beat_bot.song_list.append(url)
    else:
        voice = ctx.voice_client
        if len(beat_bot.song_list) == 0:
            beat_bot.song_list.append(url)

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        count = beat_bot.get_counter()
        ydl.download([beat_bot.song_list[count]])
    for file in os.listdir("./"):
        if file.endswith(".mp3"):
            os.rename(file, "song.mp3")
    await ctx.send(f"Now Playing: {beat_bot.song_list[count]}")

    voice.play(discord.FFmpegPCMAudio(source="song.mp3"), after=lambda e: play_next(ctx, count))


@client.command()
async def leave(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_connected():
        await voice.disconnect()
    else:
        await ctx.send("The bot is not connected to a voice channel.")


@client.command()
async def pause(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
    else:
        ctx.send("Nothing's playing atm.")


@client.command()
async def resume(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_paused():
        voice.resume()
    else:
        await ctx.send("The audio isnt paused.")


@client.command()
async def print_list(ctx):
    await ctx.send(beat_bot.song_list)


@client.command()
async def stop(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    voice.stop()
    beat_bot.song_list.clear()
    beat_bot.set_counter(0)


@client.command()
async def clear(ctx):
    beat_bot.song_list.clear()
    await ctx.send(f"Playlist has been cleared")


@client.command()
async def next(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    voice.stop()


@client.command()
async def prev(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    count = beat_bot.get_counter() - 1
    beat_bot.set_counter(count)
    beat_bot.command = True
    voice.stop()
    if beat_bot.get_counter() + 2 == len(beat_bot.song_list) > 1:
        beat_bot.command = False
        play_next(ctx, count - 1)


@client.command()
async def get_pos(ctx):
    count = beat_bot.get_counter()
    await ctx.send(f"{count}")


def play_next(ctx, count):
    if len(beat_bot.song_list) == 0:
        asyncio.run_coroutine_threadsafe(ctx.send("Playlist stopped."), loop)
        return

    count = count + 1
    beat_bot.set_counter(count)

    if beat_bot.get_counter() == len(beat_bot.song_list) == 1:
        beat_bot.song_list.clear()
        beat_bot.set_counter(0)
        asyncio.run_coroutine_threadsafe(ctx.send("End of playlist! List cleared."), loop)

    elif beat_bot.get_counter() + 1 == len(beat_bot.song_list) > 1 and not beat_bot.command:
        song_there = os.path.isfile("song.mp3")
        try:
            if song_there:
                os.remove("song.mp3")
        except PermissionError:
            pass
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([beat_bot.song_list[count]])
        for file in os.listdir("./"):
            if file.endswith(".mp3"):
                os.rename(file, "song.mp3")
        asyncio.run_coroutine_threadsafe(ctx.send(f"Now Playing: {beat_bot.song_list[count]}"), loop)
        asyncio.run_coroutine_threadsafe(ctx.send("End of playlist! List cleared."), loop)
        beat_bot.song_list.clear()
        beat_bot.set_counter(0)
        voice.play(discord.FFmpegPCMAudio(source='song.mp3'))
    elif not beat_bot.command:
        asyncio.run_coroutine_threadsafe(play(ctx, beat_bot.song_list[count]), loop)
    else:
        beat_bot.command = False
        count = count - 2
        beat_bot.set_counter(count)
        asyncio.run_coroutine_threadsafe(play(ctx, beat_bot.song_list[count]), loop)


client.run(os.environ['TOKEN'])
