import discord
from discord.ext import commands, tasks
from discord.voice_client import VoiceClient
import requests
import json
import os
import asyncio
import youtube_dl
import random as rd 
import math
from discord.utils import get
from random import choice

# prep
token = "insert your bot token here"
intents = discord.Intents.all()
Bot = commands.Bot(command_prefix='colu ', intents=intents)

#ffmpeg prep
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


# declare variable lists
songlist = []
detect = False
loop = False
queue = []


# event and command lists
@Bot.event
async def on_ready():
    print(f"I, {Bot.user}, is ready to serve master")


@Bot.command(name='join', help='This command makes the bot join the voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("not in a voice channel arent you.")
        return
    else:
        channel = ctx.message.author.voice.channel
    await channel.connect()




@Bot.command(pass_context=True)
async def p(ctx, *args):
    global voice_clients
    global yt_dl_opts
    global ffmpeg_options
    global loop
    global songlist
    if ctx.author != Bot.user:
        if (ctx.author.voice) :
            try:
                voice_client = await ctx.message.author.voice.channel.connect()
                voice_clients[voice_client.guild.id] = voice_client
            except:
                if not ctx.author.voice:
                    await ctx.send("not in a voice channel arent you.")
                else: pass
        url = args[0]
        player = await YTDLSource.from_url(url, loop=Bot.loop)
        songlist.append(player)
        voice_clients[ctx.guild.id].play(player, after=lambda e: print('Player error: %s' % e) if e else None)
    

@Bot.command(name='play', help='This command plays music')
async def play(ctx):
    global queue
    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel")
        return
    else:
        channel = ctx.message.author.voice.channel
    try: await channel.connect()
    except: pass
    server = ctx.message.guild
    voice_channel = server.voice_client
    async with ctx.typing():
        player = await YTDLSource.from_url(queue[0], loop=Bot.loop)
        songlist.append(player)
        voice_channel.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
        if loop:
            queue.append(queue[0])
        del(queue[0])
    await ctx.send('**Now playing:** {}'.format(player.title))
    

@Bot.command(pass_context=True, help='This command pauses the song')
async def pause(ctx):
    server = ctx.message.guild
    voice_channel = server.voice_client
    voice_channel.pause()


@Bot.command(name='resume', help='This command resumes the song!')
async def resume(ctx):
    server = ctx.message.guild
    voice_channel = server.voice_client
    voice_channel.resume()


@Bot.command(name='add')
async def add(ctx, *args):
    global queue
    queue.append(args)
    await ctx.send(f'`{args}` added to queue!')


@Bot.command(name='view', help='This command shows the queue')
async def view(ctx):
    await ctx.send(f'Your queue is now :')
    respons = ""
    for i in range(len(songlist)):
        respons += f"{i+1}. {songlist[i].title} \n"
    await ctx.channel.send(f"{respons}")


@Bot.command(name='leave', help='This command stops the music and makes the bot leave the voice channel')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    await voice_client.disconnect()


@Bot.command(pass_context=True, help='loop current queue, use it to reverse the current loop status.')
async def loop(ctx):
    global loop
    if loop:
        loop = False
        await ctx.channel.send(f"loop status is now disabled.")
    else:
        loop = True
        await ctx.channel.send(f"loop status is now enabled.")


@Bot.command(pass_context=True, help="command that test the bot is on or not")
async def ping(ctx):
    if ctx.author != Bot.user:
        respons = [f"tebak sih gw udah on apa belom.", f"test mulu anjing.", f"gw pen istirahat bangsat.", f"izin off dulu.", f"iya kamu ganteng."]
        await ctx.channel.send(f"{choice(respons)} \nbtw columbina responded with latency around {round(Bot.latency * 1000)} ms")


@Bot.command(pass_context=True, help="command that enable the detecting edited message")
async def enable_feature(ctx):
    if ctx.author != Bot.user:
        global detect
        detect = True
        await ctx.channel.send(f"Detecting feature has been enabled.")    
@Bot.command(pass_context=True, help="command that disable the detecting edited message")
async def disable_feature(ctx):
    if ctx.author != Bot.user:
        global detect
        detect = False
        await ctx.channel.send(f"Detecting feature has been disabled.")


@Bot.command(pass_context=True, help="command that give you a reasonable answer to your argue \nand use '; apakah x valid' to make the bot gives a argument.")
async def apakah(ctx, *args):
    if ctx.author != Bot.user:
        valid = False
        if len(args) != 0:
            if args[len(args)-1] == 'valid':
                valid = True
        if valid:
            respons = [f"valid mint no debat.", f"tidak valid mint.", f"columbina tidak berhak memberi pendapat pada argument itu."]
            await ctx.channel.send(choice(respons))
        else:
            respons = [f"mungkin.", f"ya.", f"tidak.", f"tebak.", f"gapaham anjing.", f"pala bapakkau lah."]
            await ctx.channel.send(choice(respons))      


@Bot.command(pass_context=True, help="command that give you a reasonable answer to your argue")
async def mengapa(ctx):
    if ctx.author != Bot.user:
        respons = [f"karena kamu anjing.", f"karena nameless suka loli.", f"tanyakan kepada rumput yang bergoyang.", f"kataku mending tanya ke Yang Maha Kuasa.", f"karena kamu gay.", f"karena saya cantik."]
        await ctx.channel.send(choice(respons))


@Bot.command(pass_context=True, name="rate", help="command that judge and rate your argue")
async def rate(ctx): 
    if ctx.author != Bot.user:
        a = rd.randint(-10, 10)
        if a>=-10 and a < 0: respons = [f"momen/10", f"{math.pi}", f"420/69", f"9/11"]
        else: respons = [f"{a}/10", f"69/420"]
        await ctx.channel.send(choice(respons))


@Bot.command(pass_context=True, help="command that test your gacha luck")
async def gacha(ctx):
    if ctx.author != Bot.user:
        a = rd.randint(1,1000)
        if a == 1:
            await ctx.channel.send(f"holy shit you won the UR (0.1%), better try your gacha quickly.")
        if a > 1 and a < 12:
            await ctx.channel.send(f"you will get a SSR in your next gacha (1%).")
        elif a >= 12 and a <= 112:
            await ctx.channel.send(f"you will get a SR in your next gacha (10%).")
        elif a>112 and a <= 512:
            await ctx.channel.send(f"you will get a R in your next gacha (around 40% chance).")     
        else:
            await ctx.channel.send(f"you will get a common in your next gacha (around 50% chance).")     


@Bot.command(pass_context=True, help="rolling a slot machine")
async def slot(ctx):
    if ctx.author != Bot.user:
        await ctx.channel.send(f"rolling a slot machine for you...")
        a = [rd.randint(0,9), rd.randint(0,9), rd.randint(0,9), rd.randint(0,9), rd.randint(0,9), rd.randint(0,9), rd.randint(0,9), rd.randint(0,9), rd.randint(0,9)]
        message = await ctx.channel.send(f"{a[0]} {a[1]} {a[2]} \n{a[3]} {a[4]} {a[5]} \n{a[6]} {a[7]} {a[8]}")
        for i in range(8):
            if i < 3:
                for j in range(9):
                    a[j] = rd.randint(0,9)
            elif i < 6:
                for j in range(3,9):
                    a[j] = rd.randint(0,9)
            else:
                for j in range(6,9):
                    a[j] = rd.randint(0,9)
            await asyncio.sleep(0.1)
            await message.edit(content=f"{a[0]} {a[1]} {a[2]} \n{a[3]} {a[4]} {a[5]} \n{a[6]} {a[7]} {a[8]}")
        jackpot = False
        for i in range(0, 9, 3):
            if a[i] == a[i+1] and a[i+1] == a[i+2]:
                if not jackpot: 
                    await ctx.channel.send(f"You have a jackpot with a number {a[i]}.")
                    jackpot = True
        if not jackpot:
            await ctx.channel.send(f"You dont have any number that match.")
                   

@Bot.command(pass_context=True, help="echoes whatever you said")
async def echoes(ctx, *args):
    if ctx.author != Bot.user:
        await ctx.channel.send(f"{args}")



@Bot.event
async def on_message_edit(before, after):
    if detect:
        if before.author != Bot.user:
            if before.content != after.content: 
                await before.channel.send(
                    f"{before.author.mention} kedetect ngedit bang.\n"
                    f"Before : {before.content} \n"
                    f"After : {after.content} \n"
                )
async def on_message(msg):
    if msg.author != Bot.user:
        if msg.content.lower().startswith("valid"):
            await msg.channel.send(f"valdi")



Bot.run(token)
