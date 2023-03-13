import discord
import pickle
import subprocess
import os
import asyncio
import youtube_dl
import random as rd 
import math
import datetime
import aiohttp
import openai
from discord.ext import commands, tasks
from discord.voice_client import VoiceClient
from kitsune import Kitsune, Popularity, Tag, Artist, Character, Parody, Group 
from discord.utils import get
from discord import app_commands
from discord_webhook import DiscordWebhook, DiscordEmbed
from random import choice
from pytube import YouTube



preflist = pickle.load(open("preflist.dat", "rb"))

# prep
token = " "
apikeys = " "
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
    'source_address': '0.0.0.0' 
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
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


# declare variable
songlist = []
detect = False
loop = False
queue = []
taglist = pickle.load(open("taglist.dat", "rb"))
attlist = pickle.load(open("attlist.dat", "rb"))


# BOT event and commands


@Bot.event
async def on_ready():   
    print(f"I, {Bot.user}, is ready to serve master")
    try:
        synced = await Bot.tree.sync()
        print(f"synced {len(synced)} slash command!")
    except Exception as e:
        print(e)

    
# Tree Command Lists
@Bot.tree.command(name="hello", description="greeting the user with latency ")
async def test(interaction: discord.Interaction):
    await interaction.response.send_message(f"> Hey! {interaction.user.mention} \n> btw Columbina responded with latency around {round(Bot.latency * 1000)} ms")


@Bot.tree.command(name="ping", description="ping the user with random message and latency")
async def ping(interaction: discord.Interaction):
    respons = [f"tebak sih gw udah on apa belom.", f"test mulu anjing.", f"gw pen istirahat bangsat.", f"izin off dulu.", f"iya kamu ganteng."]
    await interaction.response.send_message(f"> {choice(respons)} \n> btw columbina responded with latency around {round(Bot.latency * 1000)} ms")


@Bot.tree.command(name="say", description="I will say anything you want me to say!")
@app_commands.describe(thing_to_say = "Sentence that i will say", att_to_say = "Attachment to be send")
async def say(interaction: discord.Interaction, thing_to_say: str, att_to_say: discord.Attachment = None):
    embed = discord.Embed(
        colour=discord.Colour.random(),
        description=thing_to_say,
        title="Columbina submitted fess!")
    if att_to_say is not None:
        embed.set_image(url=att_to_say.url) 
    embed.set_footer(text=f"Today at {datetime.datetime.now().hour}:{datetime.datetime.now().minute}")
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message(f"your fess has been send!", ephemeral=True)


@Bot.tree.command(name="audio", description="Downloading audio from the given youtube link!")
@app_commands.describe(youtube_link_to_download = "Youtube link that i will download the audio")
async def audio(interaction: discord.Interaction, youtube_link_to_download: str):
    await interaction.response.defer(thinking=False)
    title = YouTube(youtube_link_to_download).title
    title = title.replace('\\',"").replace('/',"").replace(':',"").replace('*',"").replace('?',"").replace('"',"").replace('<',"").replace('>',"").replace('|',"").replace(".","")
    youtubeObject = YouTube(youtube_link_to_download)
    youtubeObject = youtubeObject.streams.get_by_itag(18)
    youtubeObject.download()
    subprocess.run(f'ffmpeg -i "{title}".mp4 "{title}".mp3', shell=True)
    await interaction.followup.send("Sorry for waiting! here is the file!",file=discord.File(f"{title}.mp3"))
    os.remove(f"{title}.mp4")
    os.remove(f"{title}.mp3")


@Bot.tree.command(name="video", description="Downloading video from the given youtube link!")
@app_commands.describe(youtube_link_to_download = "Youtube video link that i will download")
async def video(interaction: discord.Interaction, youtube_link_to_download: str):
    await interaction.response.defer(thinking=False)
    title = YouTube(youtube_link_to_download).title
    title = title.replace('\\',"").replace('/',"").replace(':',"").replace('*',"").replace('?',"").replace('"',"").replace('<',"").replace('>',"").replace('|',"")
    youtubeObject = YouTube(youtube_link_to_download)
    youtubeObject = youtubeObject.streams.get_by_itag(18)
    youtubeObject.download()
    await interaction.followup.send("Sorry for waiting! here is the file!", file=discord.File(f"{title}.mp4"))
    os.remove(f"{title}.mp4")   


@Bot.tree.command(name="tag", description="Adding tag, removing tag, or see the tag lists.") 
@app_commands.describe(add_remove_list = "argument that you want to proceed", tag="tag that you want to remove or add", stringtag="tag that you want to add", attachtag="attachment tag that you want to add")
async def tag(interaction: discord.Interaction, add_remove_list: str, tag: str = None, stringtag: str = None, attachtag: discord.Attachment = None):   
    if add_remove_list == 'add' and (tag is not None) and (stringtag is not None or attachtag is not None):
        sama = False
        for i in taglist:
            if tag == i:
                sama = True
        if sama == False:
            successfull = False
            if attachtag is not None:
                attlist.append(attachtag.url)
                pickle.dump(attlist, open("attlist.dat", "wb"))
                await interaction.response.send_message(f"tag **{tag}** successfully registered")
                successfull = True
            else:
                attlist.append(stringtag)
                pickle.dump(attlist, open("attlist.dat", "wb"))
                await interaction.response.send_message(f"tag **{tag}** successfully registered")
                successfull = True
            if successfull:
                taglist.append(tag)
                pickle.dump(taglist, open("taglist.dat", "wb"))
        else:
            await interaction.response.send_message(f"tag **{tag}** has been registered before")
    elif add_remove_list == 'remove' and (tag is not None):
        rem = True
        for i in range(len(taglist)):
            if tag == taglist[i]:
                taglist.remove(taglist[i])
                pickle.dump(taglist, open("taglist.dat", "wb"))
                attlist.remove(attlist[i])
                pickle.dump(attlist, open("attlist.dat", "wb"))
                await interaction.response.send_message(f"tag **{tag}** successfully removed.")
                rem = False
                break
        if rem: 
            await interaction.response.send_message(f"tag **{tag}** not found.")
    elif add_remove_list == "list":
        msg = ""
        for i in taglist:
            msg += i; msg += ", "
        await interaction.response.send_message(
            f"list has been registered: "
            f"```{msg}```"
        )
    else:
        await interaction.response.send_message(f"Command argument is not valid!")


@Bot.tree.command(name="devannounce", description="making discord webhook announcement")
@app_commands.describe(announce="announcement to be announce")
async def announce(interaction: discord.Interaction, announce: str):
    webhook = DiscordWebhook(" ", username="Columbina Announcment", content="Tes")
    embed = discord.Embed(
        colour=discord.Colour.dark_green()
        )
    embed.set_author(name=interaction.guild.name)
    embed.add_embed_field(name="Description", value="tes")
    webhook.add_embed(embed)
    await interaction.response.send_message(embed)


@Bot.tree.command(name="chatgpt", description="Chat GPT based command!")
@app_commands.describe(question="Ask me anything!")
async def chatgpt(interaction: discord.Interaction, question: str):
    await interaction.response.defer(thinking=False)
    async with aiohttp.ClientSession() as session:
        payload = {
            "model": "text-davinci-003",
            "prompt": question,
            "temperature": 0.5,
            "max_tokens": 1000, 
            "presence_penalty": 0,
            "frequency_penalty": 0,
            "best_of": 1,
        }
        headers = {"Authorization": f"Bearer {apikeys}"}
        async with session.post("https://api.openai.com/v1/completions", json=payload, headers=headers) as resp:
            response = await resp.json()
            try:
                urls = interaction.user.guild_avatar.url
            except:
                urls = interaction.user.avatar.url
            embed = discord.Embed(colour=discord.Colour.random(),title="AI Generated Responses", description=response["choices"][0]["text"]).set_footer(text=f"Today at {datetime.datetime.now().hour}:{datetime.datetime.now().minute}", icon_url=urls)
            await interaction.followup.send(embed=embed)    


@Bot.tree.command(name="avatar", description="Get avatar of the user who selected")
@app_commands.describe(user="Tag the user who want to get the avatar!")
async def avatar(interaction: discord.Interaction, user: discord.User):
    try:
        embed = discord.Embed(title=f"{user}'s avatar!", colour=discord.Colour.random())
        try:    
            urls = user.guild_avatar.url
        except:
            urls = user.avatar.url
        embed.set_image(url=urls)
        embed.set_footer(text=f"Today at {datetime.datetime.now().hour}:{datetime.datetime.now().minute}")
        await interaction.response.send_message(embed=embed)    
    except:
        await interaction.response.send_message(f"please give the proper mention!", ephemeral=True)


# Ordinary Command Lists
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
    await ctx.send(f'**Now playing:** {player.title}')
    

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


@Bot.command(pass_context=True)
async def test(ctx):
    if ctx.author != Bot.user:
        await ctx.channel.send(ctx.guild.id)


@Bot.command(pass_context=True)
async def ohayo(ctx, *args):
    if str(ctx.author) == "NameLess#6969":
        await ctx.channel.send(f"Sending good morning message in {args[0]} hour(s) {args[1]} minute(s) and {args[2]} second(s).")
        await asyncio.sleep(int(args[0])*3600 + int(args[1])*60 + int(args[2]))
        channel = Bot.get_channel(1043863420216295455)
        responsgif = [f"https://tenor.com/view/w-arknights-arknights-dance-gif-25199998", f"https://tenor.com/view/wenomechainsama-nivar-lllll10-gif-25746616", f"https://tenor.com/view/indo-wibu-niko-niko-nii-gif-21581009", f"https://tenor.com/view/wota-jkt48-heavy-rotation-dance-weeb-gif-17745804", f"https://tenor.com/view/welcome-to-otaku-weeb-goopie-gif-19387818", f"https://tenor.com/view/happy-happy-dog-dog-happiest-dog-super-happy-gif-17885812", f"https://tenor.com/view/segs-man-phase2-segs-man-segs-takeshi-%E3%81%B5%E3%81%BF%E3%83%BC%E3%82%93-gif-23702698", f"https://tenor.com/view/kermit-kermitreee-kermit-aaaaa-scream-gif-15959515", f"https://tenor.com/view/captain-price-cod-modern-warfare-price-dancing-gif-21612770"]
        responschat = [f"Good morning yall, time to survive another day.", f"Ohayou sekai good morning world~!"]
        responschat2 = [f"Dont forget to have a breakfast!", f"Dont forget to take your daily dose of copium!"]
        await channel.send(
            f"{choice(responschat)}\n"
            f"{choice(responschat2)}\n") 
        await channel.send(f"{choice(responsgif)}")
    else:
        await ctx.channel.send(f"This feature is Developer only, you are not my husband.")

        

    



@Bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.channels, name='「💬」general')
    await channel.send(f'Irashaimasee {member.mention}-san! gohan ni suru? ofuro ni suru? soredomo? wa-ta-shi?')
    await channel.send(f"https://cdn.discordapp.com/attachments/1043863420216295455/1064740380408565760/WelcomingPNG.jpg")


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
        msg = []
        for i in ctx.content.split(' '):
            if len(i) > 2:
                if i[0] == '#' and i[len(i)-1] == '#':
                    tagused = True
                    msg.append(i[1:len(i)-1])
        if tagused: 
            notfound = True
            for j in range(len(msg)):
                for i in range(len(taglist)):
                    if msg[j] == taglist[i]:
                        await ctx.channel.send(f"{attlist[i]}")
                        notfound = False
                    
            if notfound:    
                await ctx.channel.send(f"tag **{msg}** has not been registered yet.")
        else:
            if "tiga" in ctx.content.lower():
                await ctx.reply("wait, **TIGA???**")
            elif "beliau" in ctx.content.lower():
                await ctx.reply(choice([f"https://cdn.discordapp.com/attachments/1063877319724372052/1069245845838516234/0.png", f"https://cdn.discordapp.com/attachments/1063877319724372052/1069245845838516234/0.png", f"https://cdn.discordapp.com/attachments/1063877319724372052/1069245957096616037/FahuWR8UEAE1_sU.png", f"https://cdn.discordapp.com/attachments/1063877319724372052/1069246054513528882/7e02b4790efc8b12a176a216b1e5fa93.png", f"https://cdn.discordapp.com/attachments/1063877319724372052/1069246155604631552/2Q.png", f"https://cdn.discordapp.com/attachments/1063877319724372052/1069246220268216422/FaHppUjacAIWm5-.png"]))
            await Bot.process_commands(ctx)


    




Bot.run(token)  
