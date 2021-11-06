import os
import discord
#import youtube_dl
import yt_dlp
from discord.ext import commands
import asyncio

# bot class to hold playlist and index counter
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


# initialize event loop for async routines
loop = asyncio.get_event_loop()

# initialize bot command prefixes
client = commands.Bot(command_prefix=["!", "&", "-"])

# initialize bot
beat_bot = bot()


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.command()
async def play(ctx, url: str): # play command
    await asyncio.sleep(.5) # sleep for .5 secs
    song_there = os.path.isfile("song.mp3") # checks to see if file exists
    try:
        if song_there: 
            os.remove("song.mp3") # if file exists, delete it
    except PermissionError:
        beat_bot.song_list.append(url)  # if app is using file, add new url to queue
        await ctx.send("Song added to queue")
        return

    voice_channel = ctx.author.voice.channel # get authors voice channel

    if ctx.voice_client is None:
        voice = await voice_channel.connect()
        beat_bot.song_list.append(url)
    else:
        voice = ctx.voice_client # join channel
        if len(beat_bot.song_list) == 0:
            beat_bot.song_list.append(url) # append URL if list empty

    ydl_opts = { # youtube download options
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        count = beat_bot.get_counter() # get index
        ydl.download([beat_bot.song_list[count]]) # download YT link
    for file in os.listdir("./"):
        if file.endswith(".mp3"):
            os.rename(file, "song.mp3") # change file name to 'song.mp3'
    await ctx.send(f"Now Playing: {beat_bot.song_list[count]}") # output title

    # play song, ready auto-play lambda
    voice.play(discord.FFmpegPCMAudio(source="song.mp3"), after=lambda e: play_next(ctx, count))


@client.command()
async def leave(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_connected():
        await voice.disconnect() # leave voice channel
    else:
        await ctx.send("The bot is not connected to a voice channel.")


@client.command()
async def pause(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.pause() # pause song
    else:
        ctx.send("Nothing's playing atm.")


@client.command()
async def resume(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_paused():
        voice.resume() # resume song
    else:
        await ctx.send("The audio isnt paused.")


@client.command()
async def print_list(ctx):
    await ctx.send(beat_bot.song_list) # pring queue list


@client.command()
async def stop(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    voice.stop() # stop playlist
    beat_bot.song_list.clear() # clear playlist
    beat_bot.set_counter(0) # set index to 0


@client.command()
async def clear(ctx):
    beat_bot.song_list.clear() # clear playlist
    await ctx.send(f"Playlist has been cleared")


@client.command()
async def next(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    voice.stop() # stops song, triggers lambda in Play()


@client.command()
async def prev(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    count = beat_bot.get_counter() - 1 # decrement counter
    beat_bot.set_counter(count) # set counter
    beat_bot.command = True # set bool to true
    voice.stop() # stop song, triggers lambda in Play()
    if beat_bot.get_counter() + 2 == len(beat_bot.song_list) > 1:
        beat_bot.command = False
        play_next(ctx, count - 1) # plays prev


@client.command()
async def get_pos(ctx):
    count = beat_bot.get_counter()
    await ctx.send(f"{count}") # output current index position


def play_next(ctx, count):
    if len(beat_bot.song_list) == 0: # checks if list is empty
        asyncio.run_coroutine_threadsafe(ctx.send("Playlist stopped."), loop) 
        return

    count = count + 1 # inc index
    beat_bot.set_counter(count) # set index

    if beat_bot.get_counter() == len(beat_bot.song_list) == 1:
        beat_bot.song_list.clear() # clear list 
        beat_bot.set_counter(0) # set index
        asyncio.run_coroutine_threadsafe(ctx.send("End of playlist! List cleared."), loop)

    elif beat_bot.get_counter() + 1 == len(beat_bot.song_list) > 1 and not beat_bot.command:
        song_there = os.path.isfile("song.mp3")
        try:
            if song_there:
                os.remove("song.mp3") # removes file if exists
        except PermissionError:
            pass
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild) # gets suthors voice channel

        ydl_opts = { # youtube download options
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([beat_bot.song_list[count]]) # downloads YT link
        for file in os.listdir("./"):
            if file.endswith(".mp3"):
                os.rename(file, "song.mp3") # renames download
        asyncio.run_coroutine_threadsafe(ctx.send(f"Now Playing: {beat_bot.song_list[count]}"), loop)
        asyncio.run_coroutine_threadsafe(ctx.send("End of playlist! List cleared."), loop)
        beat_bot.song_list.clear() # clears list
        beat_bot.set_counter(0) # sets index
        voice.play(discord.FFmpegPCMAudio(source='song.mp3')) # calls Play()
    elif not beat_bot.command:
        asyncio.run_coroutine_threadsafe(play(ctx, beat_bot.song_list[count]), loop)
    else:
        beat_bot.command = False
        count = count - 2
        beat_bot.set_counter(count)
        asyncio.run_coroutine_threadsafe(play(ctx, beat_bot.song_list[count]), loop)


client.run(os.environ['TOKEN'])
