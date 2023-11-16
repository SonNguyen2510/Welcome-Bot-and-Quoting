import os
import random
import tempfile
from io import BytesIO
import asyncio
import discord
from gtts import gTTS
from googleapiclient.discovery import build
from google_images_search import GoogleImagesSearch
import openai
import json

TOKEN = "MTA5MDExODU5NzYwODczNDcyMA.GZZEy6.dOvD6CIobzFXkALyQ2kacvDVTZ6-_MmM1Tal-8"
API_KEY = "AIzaSyBqOPOiSPajLRb-Pzdz0_1tQSL07tgMGis"
SEARCH_ENGINE_ID = "a42cbd5fae88048e1"
OPENAI_API_KEY = "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"

# Set up the OpenAI API
openai.api_key = OPENAI_API_KEY
MODEL_ENGINE = "davinci"

def generate_response(prompt):
    response = openai.Completion.create(
        engine=MODEL_ENGINE,
        prompt=prompt,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.9,
    )
    message = response.choices[0].text.strip()
    return message

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

# Define the mapping between words and emojis
emoji_replace = {
        "sad": "sadgee",
        "lol": "lmao",
        "so": "worri",
        "go": "join",
        "mlem": "your_cum",
        "pog": "pog"
    }

# Dictionary of quotes
# Load quotes from file
quotes_file = 'quotes.json'
try:
    with open("quotes.json", "r") as f:
        quotes = json.load(f)
except json.decoder.JSONDecodeError:
    quotes = {}

# Set up the Discord bot
discord_client = discord.Client(intents=discord.Intents.all())

gis = GoogleImagesSearch(API_KEY, SEARCH_ENGINE_ID)


@discord_client.event
async def on_ready():
    print("Logged in as {0.user}".format(discord_client))

@discord_client.event
async def on_voice_state_update(member, before, after):
    if member.bot: # check if member is a bot user
        return

    if before.channel is None and after.channel is not None:
        voice_channel = after.channel
        text_channel = voice_channel.guild.text_channels[2] # assuming the first text channel in the server is the one to send welcome messages
        if voice_channel is not None:
            tts = gTTS(text=f"Hello {member.name} vào {voice_channel.name} để đì ranh", lang="vi")
            tts.save("welcome.mp3")

            emoji = discord.utils.get(discord_client.emojis, name="join")
            await text_channel.send(f"Hello, {member.name}! đã vào {voice_channel.name} {str(emoji)}")

            vc = await voice_channel.connect()
            source = discord.FFmpegPCMAudio("welcome.mp3")
            vc.play(source)

            while vc.is_playing():
                await asyncio.sleep(1)

            await vc.disconnect()

            os.remove("welcome.mp3")

@discord_client.event
async def on_message(message):
    if message.author == discord_client.user:
        return

    if message.content.startswith('!pa help'):
        help_message = """
        Here are the available commands:
        - !hello - Say hello to the bot
        - !search <query> - Search Google for <query>
        - !chat <prompt> - Ask the bot to generate a response based on <prompt>
        - !s <text> - Have the bot speak <text> in a voice channel
        - !image <query> - Search Google Images for <query>
        - !addquote <keyword> <quote> - Add <quote> to the list of quotes 
        - !clearquote <keyword> - Clear <quote> with coresponding from the list of quotes 
        - !listquotes - List all quotes 
        - !quote <keyword> - Speak quote in the voice channel
        - !pa help - Show this help message
        """
        await message.channel.send(help_message)

    if message.content.startswith("!hello"):
        emoji = discord.utils.get(discord_client.emojis, name="lmao")
        await message.channel.send(f"Hello, {message.author.mention}! {str(emoji)}")

    if message.content.startswith("!search"):
        query = message.content[7:]
        result = google_search(query)
        await message.channel.send(result)

    if message.content.startswith("!chat"):
        response = generate_response(message.content)
        await message.channel.send(response)

    if message.content.startswith('!s'):
        text = message.content[2:]

        # Generate the TTS audio and save it to a temporary file
        language = 'vi'
        tts = gTTS(text=text, lang=language)
        with tempfile.NamedTemporaryFile(delete=False) as f:
            tts.write_to_fp(f)
            temp_file_path = f.name

        # Play the audio file in the voice channel
    # Check if bot is already connected to a voice channel
        if message.author.voice and message.author.voice.channel and message.guild.voice_client:
            if message.guild.voice_client.channel == message.author.voice.channel:
                return
            else:
                await message.guild.voice_client.move_to(message.author.voice.channel)
        else:
            vc = await message.author.voice.channel.connect()
            source = discord.FFmpegPCMAudio(temp_file_path)
            vc.play(source)
            while vc.is_playing():
                await asyncio.sleep(1)
            await vc.disconnect()

        # Delete the temporary file
        os.remove(temp_file_path)

    if message.content.startswith('!image'):
        query = message.content[6:]
        gis.search({'q': query})
        for image in gis.results():
            await message.channel.send(image.url)
            break
        else:
            await message.channel.send('No results found.')
    
    if message.content.startswith('!addquote'):
        args = message.content.split(' ', 2)
        if len(args) != 3:
            await message.channel.send('Invalid command format. Usage: !addquote keyword "quote"')
            return
        
        keyword, quote = args[1], args[2].strip('"')
        try:
            with open("quotes.json", "r") as f:
                quotes = json.load(f)
        except json.decoder.JSONDecodeError:
            quotes = {}
        
        if keyword in quotes:
            await message.channel.send(f'Quote with keyword "{keyword}" already exists')
            return
        
        quotes[keyword] = quote
        with open(quotes_file, 'w') as f:
            json.dump(quotes, f)
        
        await message.channel.send(f'Added new quote with keyword "{keyword}"')
    
    elif message.content.startswith('!clearquote'):
        args = message.content.split(' ')
        if len(args) != 2:
            await message.channel.send('Invalid command format. Usage: !clearquote keyword')
            return
        
        keyword = args[1]
        try:
            with open("quotes.json", "r") as f:
                quotes = json.load(f)
        except json.decoder.JSONDecodeError:
            quotes = {}
        
        if keyword not in quotes:
            await message.channel.send(f'No quote found with keyword "{keyword}"')
            return
        
        del quotes[keyword]
        with open(quotes_file, 'w') as f:
            json.dump(quotes, f)
        
        await message.channel.send(f'Quote with keyword "{keyword}" has been deleted')
    
    elif message.content.startswith('!listquotes'):
        try:
            with open("quotes.json", "r") as f:
                quotes = json.load(f)
        except json.decoder.JSONDecodeError:
            quotes = {}
        if not quotes:
            await message.channel.send('No quotes found')
            return
        
        response = 'Current quotes:\n'
        for keyword, quote in quotes.items():
            response += f'**{keyword}** - "*{quote}*"\n'
        qoute_text = '\n>>> {}'.format(response)
        
        await message.channel.send(qoute_text)
    
    elif message.content.startswith('!quote'):
        args = message.content.split(' ')
        if len(args) != 2:
            await message.channel.send('Invalid command format. Usage: !quote keyword')
            return
        
        keyword = args[1]
        try:
            with open("quotes.json", "r") as f:
                quotes = json.load(f)
        except json.decoder.JSONDecodeError:
            quotes = {}
        
        if keyword not in quotes:
            await message.channel.send(f'No quote found with keyword "{keyword}"')
            return
        
        quote = quotes[keyword]
        tts = gTTS(text=quote, lang='vi')
        with tempfile.NamedTemporaryFile(delete=False) as f:
            tts.write_to_fp(f)
            temp_file_path = f.name
        
        if os.path.isfile(keyword + '.mp3') and random.random() > 0.45:
            temp_file_path = keyword + '.mp3'
            emoji = discord.utils.get(discord_client.emojis, name="pirate")
            await message.channel.send(f"Congratulate {message.author.mention}! You found a hidden treasure {str(emoji)}")
        # Play the audio file in the voice channel
        if message.author.voice:
            voice_channel = message.author.voice.channel
            vc = await voice_channel.connect()
            source = discord.FFmpegPCMAudio(temp_file_path)
            vc.play(source)
            while vc.is_playing():
                await asyncio.sleep(1)
            await vc.disconnect()

    if message.content == "!emo":
        emo_list = []
        for word, emoji_name in emoji_replace.items():
            emoji = discord.utils.get(discord_client.emojis, name=emoji_name)
            emo_list.append(f"**{word}**: {(emoji)}")
        emo_list_str = "\n".join(emo_list)
        await message.channel.send(f"List of replaceable words and corresponding emojis:\n{emo_list_str}")

    replaced_message = await replace_with_emoji(message)
    if replaced_message:
        print("Replaced user message with custom emoji")

    # await emoji_replace(message)

if __name__ == '__main__':
    # Replace "your_token_here" with your actual bot token
    discord_client.run(TOKEN)
