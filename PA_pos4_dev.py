import os
import random
import tempfile
from io import BytesIO
import asyncio
import discord
from gtts import gTTS
import json
from discord.ext import commands
from googleapiclient.discovery import build
# from google_images_search import GoogleImagesSearch

API_KEY = "AIzaSyBqOPOiSPajLRb-Pzdz0_1tQSL07tgMGis"
SEARCH_ENGINE_ID = "a42cbd5fae88048e1"
TOKEN = "MTA5MDExODU5NzYwODczNDcyMA.GZZEy6.dOvD6CIobzFXkALyQ2kacvDVTZ6-_MmM1Tal-8"

quotes_file = 'quotes.json'
try:
    with open(quotes_file, "r") as f:
        quotes = json.load(f)
except json.decoder.JSONDecodeError:
    quotes = {}

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=";", intents=intents)
# gis = GoogleImagesSearch(API_KEY, SEARCH_ENGINE_ID)

emoji_replace = {
    "sad": "sadgee",
    "lol": "lmao",
    "so": "worri",
    "go": "join",
    "mlem": "your_cum",
    "pog": "pog"
}

def google_search(query):
    service = build("customsearch", "v1", developerKey=API_KEY)
    try:
        res = service.cse().list(q=query, cx=SEARCH_ENGINE_ID).execute()
        if "items" in res:
            return res["items"][0]["link"]
        else:
            return "No results found."
    except Exception as e:
        print(f"An error occurred while searching Google: {e}")
        return "An error occurred while searching Google."
    
async def replace_with_emoji(message):
    if message.content in emoji_replace:
        # create webhook for the channel
        webhook = await message.channel.create_webhook(name="Emoji Bot")
        # get the user's name and avatar
        user_name = message.author.display_name
        user_avatar = message.author.avatar
        # send the message with webhook
        await webhook.send(str(discord.utils.get(message.guild.emojis, name=emoji_replace[message.content])), username=user_name, avatar_url=user_avatar)
        # delete the original message
        await message.delete()
        # delete the webhook
        await webhook.delete()
        return True
    return False

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    replaced_message = await replace_with_emoji(message)
    if replaced_message:
        print("Replaced user message with custom emoji")
    else:
        await bot.process_commands(message)

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot or before.channel is not None:
        return

    voice_channel = after.channel
    text_channel = voice_channel.guild.text_channels[2]

    tts = gTTS(text=f"Hello {member.display_name} vào {voice_channel.name} để đì ranh", lang="vi")
    tts.save("welcome.mp3")

    emoji = discord.utils.get(bot.emojis, name="join")
    await text_channel.send(f"Hello, {member.display_name}! đã vào {voice_channel.name} {str(emoji)}")

    vc = await voice_channel.connect()
    # voice_text = random.choice(["hello_handsome.mp3", "Oniichan.mp3", "welcome.mp3", "Oniichan2.mp3"])
    source = discord.FFmpegPCMAudio("welcome.mp3")
    vc.play(source)

    # source = discord.FFmpegPCMAudio("welcome.mp3")
    # vc.play(source)

    while vc.is_playing():
        await asyncio.sleep(1)

    await vc.disconnect()
    os.remove("welcome.mp3")

@bot.command(name="hello")
async def hello(ctx):
    emoji = discord.utils.get(ctx.guild.emojis, name="lmao")
    await ctx.send(f"Hello, {ctx.author.mention}! {str(emoji)}")

@bot.command(name="search")
async def search(ctx, *, query):
    result = google_search(query)
    await ctx.send(result)

# @bot.command(name="image")
# async def image(ctx, *, query):
#     gis.search({'q': query})
#     for image in gis.results():
#         await ctx.send(image.url)
#         break
#     else:
#         await ctx.send('No results found.')

@bot.command(name="s")
async def s(ctx, *, text):
    if not ctx.author.voice:
        await ctx.send('You must be in a voice channel to use this command.')
        return
    language = 'vi'
    tts = gTTS(text=text, lang=language)
    with tempfile.NamedTemporaryFile(delete=False) as f:
        tts.write_to_fp(f)
        temp_file_path = f.name

    vc = ctx.voice_client
    if not vc:
        vc = await ctx.author.voice.channel.connect()

    source = discord.FFmpegPCMAudio(temp_file_path)
    vc.play(source)

    while vc.is_playing():
        await asyncio.sleep(1)

    os.remove(temp_file_path)
    await vc.disconnect()

@s.error
async def s_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Please provide text to say.')
    else:
        await ctx.send('An error occurred.')

@bot.command(name="addq")
async def addq(ctx, keyword: str, *, quote: str):
    if keyword in quotes:
        await ctx.send(f'Quote with keyword "{keyword}" already exists')
        return
        
    quotes[keyword] = quote.strip('"')
    with open("quotes.json", "w") as f:
        json.dump(quotes, f)
        
    await ctx.send(f'Added new quote with keyword "{keyword}"')

@bot.command(name="clearq")
async def clearq(ctx, keyword: str):
    if keyword not in quotes:
        await ctx.send(f'No quote found with keyword "{keyword}"')
        return

    del quotes[keyword]
    with open(quotes_file, 'w') as f:
        json.dump(quotes, f)

    await ctx.send(f'Quote with keyword "{keyword}" has been deleted')

@clearq.error
async def clearq_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Invalid command format. Usage: !clearq keyword')
    else:
        raise error

@bot.command(name="listq")
async def listq(ctx):
    if not quotes:
        await ctx.send('No quotes found')
        return

    response = 'Current quotes:\n'
    for keyword, quote in quotes.items():
        response += f'**{keyword}** - "*{quote}*"\n'
    qoute_text = '\n>>> {}'.format(response)

    await ctx.send(qoute_text)

@bot.command(name="q")
async def quote(ctx, keyword: str):
    if keyword not in quotes:
        await ctx.send(f'No quote found with keyword "{keyword}"')
        return

    quote = quotes[keyword]
    tts = gTTS(text=quote, lang='vi')

    if os.path.isfile('quotes/' + keyword + '.mp3') and random.random() > 0.45:
        temp_file_path = 'quotes/' + keyword + '.mp3'
        emoji = discord.utils.get(bot.emojis, name="pirate")
        await ctx.send(f"Congratulate {ctx.author.mention}! You found a hidden treasure {str(emoji)}")
    else:
        with tempfile.NamedTemporaryFile(delete=False) as f:
            tts.write_to_fp(f)
            temp_file_path = f.name


    if ctx.author.voice:
        voice_channel = ctx.author.voice.channel
        vc = await voice_channel.connect()
        source = discord.FFmpegPCMAudio(temp_file_path)
        vc.play(source)
        while vc.is_playing():
            await asyncio.sleep(1)
        await vc.disconnect()

@bot.command(name='emo')
async def emoji_list(ctx):
    emo_list = []
    for word, emoji_name in emoji_replace.items():
        emoji = discord.utils.get(bot.emojis, name=emoji_name)
        emo_list.append(f"**{word}**: {(emoji)}")
    emo_list_str = "\n".join(emo_list)
    await ctx.send(f"List of replaceable words and corresponding emojis:\n{emo_list_str}")


if __name__ == '__main__':
    bot.run(TOKEN)