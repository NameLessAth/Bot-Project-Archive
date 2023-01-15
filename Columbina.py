import discord
import pickle
import os
import asyncio
import youtube_dl
import random as rd 
import math
from discord.ext import commands, tasks
from discord.voice_client import VoiceClient
from discord.utils import get
from random import choice


preflist = pickle.load(open("preflist.dat", "rb"))

# prep
token = "bot token"
intents = discord.Intents.all()
Bot = commands.Bot(command_prefix=preflist, intents=intents)



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
    def __init__(self, source, *, data, volume=0.05):
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
taglist = pickle.load(open("taglist.dat", "rb"))
attlist = pickle.load(open("attlist.dat", "rb"))




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
async def play(ctx, *args):
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
        player = await YTDLSource.from_url(args[0], loop=Bot.loop)
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
        for i in args:
            await ctx.channel.send(f"{i}")


@Bot.command(pass_context=True, help="register tag and pop the tag registered. tag add, remove, list.")
async def tag(ctx, *args):
    if ctx.author != Bot.user:
        if args[0] == "add":
            sama = False
            for i in taglist:
                if args[1] == i:
                    sama = True
            if sama == False:
                taglist.append(args[1])
                pickle.dump(taglist, open("taglist.dat", "wb"))
                try:
                    attlist.append(ctx.message.attachments[0].url)
                    pickle.dump(attlist, open("attlist.dat", "wb"))
                except:
                    msg = ""
                    for i in range(2, len(args)):
                        msg += args[i]; msg += " "
                    attlist.append(msg)
                    pickle.dump(attlist, open("attlist.dat", "wb"))
                await ctx.channel.send(f"tag **{args[1]}** successfully registered.")
            else: 
                await ctx.channel.send(f"tag **{args[1]}** has registered before.")
        elif args[0] == "list":
            msg = ""
            for i in taglist:
                msg += i; msg += ", "
            await ctx.channel.send(
                f"list that has been registered: "
                f"```{msg}```"
            )
        elif args[0] == "remove":
            rem = True
            for i in range(len(taglist)):
                if args[1] == taglist[i]:
                    taglist.remove(taglist[i])
                    pickle.dump(taglist, open("taglist.dat", "wb"))
                    attlist.remove(attlist[i])
                    pickle.dump(attlist, open("attlist.dat", "wb"))
                    await ctx.channel.send(f"tag **{args[1]}** successfully removed.")
                    rem = False
                    break
            if rem:
                await ctx.channel.send(f"tag **{args[1]}** not found.")
        else:
            notfound = True
            for i in range(len(taglist)):
                if args[0] == taglist[i]:
                    await ctx.channel.send(f"{attlist[i]}")
                    notfound = False
                    break
            if notfound:
                await ctx.channel.send(f"tag **{args[0]}** has not been registered yet.")

                
@Bot.command(pass_context=True, help="manage prefixes. prefixes add, list, remove.")
async def prefixes(ctx, *args):
    if ctx.author != Bot.user:
        if args[0] == "add":
            preflist.append(args[1])
            pickle.dump(preflist, open("preflist.dat", "wb"))
            await ctx.channel.send(f"prefixes '{args[1]}' has been added.")
        elif args[0] == "list":
            msg = ""
            for i in preflist:
                msg += "'" + i + "' "
            await ctx.channel.send(f"```{msg}```")
        elif args[0] == "remove":
            for i in range(len(preflist)):
                rem = True
                if args[1] == preflist[i]:
                    preflist.remove(preflist[i])
                    pickle.dump(preflist, open("preflist.dat", "wb"))
                    await ctx.channel.send(f"prefixes '{args[1]}' successfully removed.")
                    rem = False
            if rem:
                await ctx.channel.send(f"prefixes '{args[1]}' has not been registered yet.")
            

@Bot.command(pass_context=True, help="remind user within x seconds")
async def remind(ctx, *args):
    if ctx.author != Bot.user:
        await ctx.channel.send(f"i will mention you, {ctx.author.mention}, within {args[0]} hour(s) {args[1]} minute(s) {args[2]} second(s)")
        await asyncio.sleep(int(args[0])*3600 + int(args[1])*60 + int(args[2]))
        await ctx.channel.send(f"{ctx.author.mention} onii-chan bangun, katanya minta di ingetin.")
        await asyncio.sleep(3)
        await ctx.channel.send(f"{ctx.author.mention} mooo, onii-chan teba.")

        
@Bot.command(pass_context=True, help="sending user a mp3 version of provided youtube link.")
async def audio(ctx, *args):
    if ctx.author != Bot.user:
        title = YouTube(args[0]).title
        await ctx.reply(f"trying to download the **{title}** audio...")
        async with ctx.typing():
            youtubeObject = YouTube(args[0])
            youtubeObject = youtubeObject.streams.get_by_itag(18)
            youtubeObject.download()
            subprocess.run(f'ffmpeg -i "path\{title}".mp4 "path\{title}".mp3', shell=True)
            await ctx.reply(file=discord.File(f"path\{title}.mp3"))
            os.remove(f"path\{title}.mp4")
            os.remove(f"path\{title}.mp3")

            
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

@Bot.event
async def on_message(ctx):
    if ctx.author != Bot.user:
        tagused = False
        for i in ctx.content.split(' '):
            if i[0] == '#' and i[len(i)-1] == '#':
                tagused = True; msg = i.replace('#', ''); break
        if tagused:
            notfound = True
            for i in range(len(taglist)):
                if msg == taglist[i]:
                    await ctx.channel.send(f"{attlist[i]}")
                    notfound = False
                    break
            if notfound:
                await ctx.channel.send(f"tag **{msg}** has not been registered yet.")
        else:
            await Bot.process_commands(ctx)


Bot.run(token)
