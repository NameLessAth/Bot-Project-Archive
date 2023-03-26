import discord
import pickle
import subprocess
import os
import asyncio
import random as rd 
import math
import datetime
import aiohttp
import openai
from discord.ext import commands, tasks
from discord.voice_client import VoiceClient
from discord.utils import get
from discord import app_commands
from discord_webhook import DiscordWebhook, DiscordEmbed
from random import choice
from pytube import YouTube


preflist = pickle.load(open("preflist.dat", "rb"))

# prep
token = ""
apikeys = ""
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=preflist, intents=intents)

# declare variable
detect = False
taglist = pickle.load(open("taglist.dat", "rb"))
attlist = pickle.load(open("attlist.dat", "rb"))


# BOT event and commands
@bot.event
async def on_ready():   
    print(f"I, {bot.user}, is ready to serve master")
    try:
        synced = await bot.tree.sync()
        print(f"synced {len(synced)} slash command!")
    except Exception as e:
        print(e)

    
# Tree Command Lists
@bot.tree.command(name="hello", description="greeting the user with latency ")
async def test(interaction: discord.Interaction):
    await interaction.response.send_message(f"> Hey! {interaction.user.mention} \n> btw Columbina responded with latency around {round(bot.latency * 1000)} ms")


@bot.tree.command(name="ping", description="ping the user with random message and latency")
async def ping(interaction: discord.Interaction):
    respons = [f"tebak sih gw udah on apa belom.", f"test mulu anjing.", f"gw pen istirahat bangsat.", f"izin off dulu.", f"iya kamu ganteng."]
    await interaction.response.send_message(f"> {choice(respons)} \n> btw columbina responded with latency around {round(bot.latency * 1000)} ms")


@bot.tree.command(name="say", description="I will say anything you want me to say!")
@app_commands.describe(thing_to_say = "Sentence that i will say", att_to_say = "Attachment to be send")
async def say(interaction: discord.Interaction, thing_to_say: str, att_to_say: discord.Attachment = None):
    embed = discord.Embed(
        colour=discord.Colour.random(),
        description=thing_to_say,
        title="Columbina submitted fess!")
    if att_to_say is not None:
        embed.set_image(url=att_to_say.url) 
    embed.set_footer(text=f"Today at {datetime.datetime.now().hour:02}:{datetime.datetime.now().minute:02}")
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message(f"your fess has been send!", ephemeral=True)


@bot.tree.command(name="audio", description="Downloading audio from the given youtube link!")
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


@bot.tree.command(name="video", description="Downloading video from the given youtube link!")
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


@bot.tree.command(name="tag", description="Adding tag, removing tag, or see the tag lists.") 
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


@bot.tree.command(name="chatgpt", description="Chat GPT based command!")
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
            embed = discord.Embed(colour=discord.Colour.random(),title="AI Generated Responses", description=response["choices"][0]["text"]).set_footer(text=f"Powered by ChatGPT model Text-Davinci-003\nToday at {datetime.datetime.now().hour:02}:{datetime.datetime.now().minute:02}", icon_url="https://cdn.discordapp.com/attachments/1044425725291286579/1085875144997740564/wDxGa5utiNgg0AAAAASUVORK5CYII.png")
            await interaction.followup.send(embed=embed)    


@bot.tree.command(name="avatar", description="Get avatar of the user who selected") 
@app_commands.describe(user="Tag the user who want to get the avatar!")
async def avatar(interaction: discord.Interaction, user: discord.User):
    try:
        embed = discord.Embed(title=f"{user}'s avatar!", colour=discord.Colour.random())
        try:    
            urls = user.guild_avatar.url
        except:
            urls = user.avatar.url
        try:
            urls_req = interaction.user.guild_avatar.url
        except:
            urls_req = interaction.user.avatar.url
        embed.set_image(url=urls)
        embed.set_footer(icon_url=urls_req, text=f"Requested by {interaction.user} • Today at {datetime.datetime.now().hour:02}:{datetime.datetime.now().minute:02}")
        await interaction.response.send_message(embed=embed)    
    except:
        await interaction.response.send_message(f"please give the proper mention!", ephemeral=True)


@bot.tree.command(name="jankenpon", description="Duel the tag people to play rock, paper, scissors")
@app_commands.describe(user_to_duel="User to duel", score_to_win="Score to win the duel!")
async def jankenpon(interaction: discord.Interaction, user_to_duel: discord.User, score_to_win: int):
    if user_to_duel != interaction.user:
        berhasil = False
        await interaction.response.defer(thinking=True, ephemeral=True)
        user1score = 0; user2score = 0
        botmsg = await interaction.channel.send(f"{interaction.user.mention} challenged {user_to_duel.mention} to duel!")
        await botmsg.add_reaction(u"\u2705"); await botmsg.add_reaction(u"\u274C")
        try:
            reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user == user_to_duel, timeout=15.00)
        except:
            await interaction.channel.send(f"{user_to_duel.mention} is not replying. Duel is cancelled")
        else:
            if reaction.emoji == u"\u2705":
                await interaction.channel.send(f"GUIDE: use R/r as rock, P/p as paper, S/s as scissors, send the message after the \"==may the duel start!==\" appeared!")
                while (user1score != score_to_win and user2score != score_to_win):
                    msg = await interaction.channel.send("duel is gonna start in 5 seconds!")
                    await asyncio.sleep(2)
                    await msg.edit(content="3 seconds to the duel!") 
                    await asyncio.sleep(2)
                    await msg.edit(content="1 second remaining to the duel!")
                    await asyncio.sleep(1)
                    await msg.edit(content="==may the duel start!==") 
                    try:    
                        msg1= await bot.wait_for("message", check=lambda m: m.author == user_to_duel or m.author == interaction.user, timeout=1.7)
                        if msg1.author == user_to_duel:
                            msg2 = await bot.wait_for("message", check=lambda m: m.author == interaction.user, timeout=0.7)
                        else:
                            msg2 = await bot.wait_for("message", check=lambda m: m.author == user_to_duel, timeout=0.7)
                    except:
                        await interaction.channel.send(f"Duel is not valid! someone send his/her message too late!")
                    else:
                        if msg1.author == interaction.user:
                            if (msg1.content.lower() == "r" and msg2.content.lower() == "s") or (msg1.content.lower() == "s" and msg2.content.lower() == "p") or (msg1.content.lower() == "p" and msg2.content.lower() == "r"):
                                user1score += 1
                                await interaction.channel.send(f"{msg1.author} has won the round! (pts: {user1score})")
                            elif (msg1.content.lower() == "r" and msg2.content.lower() == "p") or (msg1.content.lower() == "s" and msg2.content.lower() == "r") or (msg1.content.lower() == "p" and msg2.content.lower() == "s"):
                                user2score += 1
                                await interaction.channel.send(f"{msg2.author} has won the round! (pts:{user2score})")
                            elif msg1.content.lower() == msg2.content.lower():
                                await interaction.channel.send(f"The round ended up draw")
                            else:
                                await interaction.channel.send(f"invalid input! use R/r or P/p or S/s only please!")
                        elif msg2.author == interaction.user:
                            if (msg1.content.lower() == "r" and msg2.content.lower() == "s") or (msg1.content.lower() == "s" and msg2.content.lower() == "p") or (msg1.content.lower() == "p" and msg2.content.lower() == "r"):
                                user2score += 1                                
                                await interaction.channel.send(f"{msg1.author} has won the round! (pts: {user2score})")
                            elif (msg1.content.lower() == "r" and msg2.content.lower() == "p") or (msg1.content.lower() == "s" and msg2.content.lower() == "r") or (msg1.content.lower() == "p" and msg2.content.lower() == "s"):
                                user1score += 1
                                await interaction.channel.send(f"{msg2.author} has won the round! (pts: {user1score})")
                            elif msg1.content.lower() == msg2.content.lower():
                                await interaction.channel.send(f"The round ended up draw")
                            else:
                                await interaction.channel.send(f"invalid input! use R/r or P/p or S/s only please!")
                if user1score == score_to_win:
                    await interaction.channel.send(f"{interaction.user}, the challenger,  has won the game!!!!")
                else:
                    await interaction.channel.send(f"{user}, the competitor, has won the game!!!!")
                berhasil = True
            else:
                await interaction.channel.send(f"{user_to_duel} is evading the duel! what a shame!")
        if berhasil:
            await interaction.followup.send(f"duel is successful")
        else:
            await interaction.followup.send(f"duel is cancelled")
    else:
        await interaction.response.send_message(f"you CANNOT duel yourself!!", ephemeral=True)


@bot.tree.command(name="roulette", description="play the game russian roulette!, getting timed out for 60 seconds if you fail the game!")
@app_commands.describe(bullet="how many bullet to put in the chamber. (1 <= bullet <= 6)")
async def roulette(interaction: discord.Interaction, bullet: int):
    if bullet >= 1 and bullet <= 6:
        await interaction.response.defer(thinking=False, ephemeral=True)
        await interaction.channel.send(f"wanna test your luck for today huh?")
        msg = await interaction.channel.send(f"choose how many times you want to spin the bullet cylinder! \nreact after the reaction added")
        await msg.add_reaction(u"\u0031\u20E3"); await msg.add_reaction(u"\u0032\u20E3"); await msg.add_reaction(u"\u0033\u20E3"); await msg.add_reaction(u"\u0034\u20E3"); await msg.add_reaction(u"\u0035\u20E3"); await msg.add_reaction(u"\u0036\u20E3")
        await interaction.channel.send(f"you might now react!")
        try:
            reaction, user = await bot.wait_for('reaction_add', check=lambda reaction, user: user == interaction.user, timeout=5)
        except:
            await interaction.channel.send(f"{interaction.user} is not replying or the input is not valid. What a loser.")
            await interaction.followup.send(f"russian roulette is cancelled.")
        else:
            kematian = [u"\u0031\u20E3", u"\u0032\u20E3", u"\u0033\u20E3", u"\u0034\u20E3", u"\u0035\u20E3", u"\u0036\u20E3"]
            kematianarr = []
            while len(kematianarr) != bullet:
                selected = choice(kematian)
                kematian.remove(selected)
                kematianarr.append(selected)
            if reaction.emoji in kematianarr:
                await interaction.user.edit(timed_out_until=discord.utils.utcnow() + datetime.timedelta(seconds=60))
                await interaction.channel.send(f"BOOM YOU GOT A BULLET LOL! TIMEOUT 60 SECS BITCH!")
            else:
                await interaction.channel.send(f"You made it!, no timeout for you!")
            await interaction.followup.send(f"russian roulette is successful")
    else:
        await interaction.response.send_message(f"Please input the right amount of bullet to input!")


# Ordinary Command Lists
@bot.command(pass_context=True, help="command that enable the detecting edited message")
async def enable_feature(ctx):
    if ctx.author != bot.user:
        global detect
        detect = True
        await ctx.channel.send(f"Detecting feature has been enabled.")    


@bot.command(pass_context=True, help="command that disable the detecting edited message")
async def disable_feature(ctx):
    if ctx.author != bot.user:
        global detect
        detect = False
        await ctx.channel.send(f"Detecting feature has been disabled.")


@bot.command(pass_context=True, help="command that give you a reasonable answer to your argue \nand use '; apakah x valid' to make the bot gives a argument.")
async def apakah(ctx, *args):
    if ctx.author != bot.user:
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


@bot.command(pass_context=True, help="command that give you a reasonable answer to your argue")
async def mengapa(ctx):
    if ctx.author != bot.user:
        respons = [f"karena kamu anjing.", f"karena nameless suka loli.", f"tanyakan kepada rumput yang bergoyang.", f"kataku mending tanya ke Yang Maha Kuasa.", f"karena kamu gay.", f"karena saya cantik."]
        await ctx.channel.send(choice(respons))


@bot.command(pass_context=True, name="rate", help="command that judge and rate your argue")
async def rate(ctx): 
    if ctx.author != bot.user:
        a = rd.randint(-10, 10)
        if a>=-10 and a < 0: respons = [f"momen/10", f"{math.pi}", f"420/69", f"9/11"]
        else: respons = [f"{a}/10", f"69/420"]
        await ctx.channel.send(choice(respons))


@bot.command(pass_context=True, help="command that test your gacha luck")
async def gacha(ctx):
    if ctx.author != bot.user:
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


@bot.command(pass_context=True, help="rolling a slot machine")
async def slot(ctx):
    if ctx.author != bot.user:
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


@bot.command(pass_context=True, help="manage prefixes. prefixes add, list, remove.")
async def prefixes(ctx, *args):
    if ctx.author != bot.user:
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
            

@bot.command(pass_context=True, help="remind user within x seconds")
async def remind(ctx, *args):
    if ctx.author != bot.user:
        await ctx.channel.send(f"i will mention you, {ctx.author.mention}, within {args[0]} hour(s) {args[1]} minute(s) {args[2]} second(s)")
        await asyncio.sleep(int(args[0])*3600 + int(args[1])*60 + int(args[2]))
        await ctx.channel.send(f"{ctx.author.mention} onii-chan bangun, katanya minta di ingetin.")
        await asyncio.sleep(3)
        await ctx.channel.send(f"{ctx.author.mention} mooo, onii-chan teba.")


@bot.command(pass_context=True)
async def test(ctx):
    if ctx.author != bot.user:
        await ctx.channel.send(ctx.guild.id)


@bot.command(pass_context=True)
async def ohayo(ctx, *args):
    if str(ctx.author) == "NameLess#6969":
        await ctx.channel.send(f"Sending good morning message in {args[0]} hour(s) {args[1]} minute(s) and {args[2]} second(s).")
        await asyncio.sleep(int(args[0])*3600 + int(args[1])*60 + int(args[2]))
        channel = bot.get_channel(1043863420216295455)
        responsgif = [f"https://tenor.com/view/w-arknights-arknights-dance-gif-25199998", f"https://tenor.com/view/wenomechainsama-nivar-lllll10-gif-25746616", f"https://tenor.com/view/indo-wibu-niko-niko-nii-gif-21581009", f"https://tenor.com/view/wota-jkt48-heavy-rotation-dance-weeb-gif-17745804", f"https://tenor.com/view/welcome-to-otaku-weeb-goopie-gif-19387818", f"https://tenor.com/view/happy-happy-dog-dog-happiest-dog-super-happy-gif-17885812", f"https://tenor.com/view/segs-man-phase2-segs-man-segs-takeshi-%E3%81%B5%E3%81%BF%E3%83%BC%E3%82%93-gif-23702698", f"https://tenor.com/view/kermit-kermitreee-kermit-aaaaa-scream-gif-15959515", f"https://tenor.com/view/captain-price-cod-modern-warfare-price-dancing-gif-21612770"]
        responschat = [f"Good morning yall, time to survive another day.", f"Ohayou sekai good morning world~!"]
        responschat2 = [f"Dont forget to have a breakfast!", f"Dont forget to take your daily dose of copium!"]
        await channel.send(
            f"{choice(responschat)}\n"
            f"{choice(responschat2)}\n") 
        await channel.send(f"{choice(responsgif)}")
    else:
        await ctx.channel.send(f"This feature is Developer only, you are not my husband.")


# Bot Event lists
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.channels, name='「💬」general')
    await channel.send(f'Irashaimasee {member.mention}-san! gohan ni suru? ofuro ni suru? soredomo? wa-ta-shi?')
    await channel.send(f"https://cdn.discordapp.com/attachments/1043863420216295455/1064740380408565760/WelcomingPNG.jpg")


@bot.event
async def on_message_edit(before, after):
    if detect:
        if before.author != bot.user:
            if before.content != after.content: 
                await before.channel.send(
                    f"{before.author.mention} kedetect ngedit bang.\n"
                    f"Before : {before.content} \n"
                    f"After : {after.content} \n"
                )


@bot.event
async def on_message(ctx):
    if ctx.author != bot.user:
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
            await bot.process_commands(ctx)



# ==RUN CODE==
bot.run(token)  
