import discord
from discord.ext import commands
import asyncio
import yt_dlp as youtube_dl
import os
import googleapiclient.discovery

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': 'songs/' + '%(title)s.%(ext)s',
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
API_KEY = "Your api key"
credential_path = "/home/sonnguyen/WORK/study/assign2/Discord_bot/credentials.json"
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class MusicPlayer:
    def __init__(self, bot):
        self.bot = bot
        self.ctx = None
        self.song_queue = []
        self.now_playing = None
        self.is_playing = False
        self.volume = 0.5
        self.youtube = googleapiclient.discovery.build('youtube', 'v3', developerKey=os.getenv("AIzaSyABR_cYe0NJlXrC4zeTF0XzovEWkeZY0lA"))


    def after_playback(error):
        if error:
            print('Error occurred:', error)
        else:
            print('Playback finished')

    async def add_song(self, url):
        """Add song to the queue and start downloading"""
        if 'youtube.com' not in url and 'youtu.be' not in url:
            url = await self.search_song(url)
            if not url:
                await self.ctx.send(f'Could not add {url} to queue.')
                return
        song_info = await self.get_song_info(url)
        self.song_queue.append(song_info)
        if self.is_playing:
            await self.ctx.send(f'Added to queue: **{song_info["title"]}**')
        else:
            self.is_playing = True
            await self.play_song()

    async def play_song(self):
        """Start playing the next song in the queue"""
        if not self.song_queue:
            self.is_playing = False
            await self.ctx.send('Queue is empty.')
            return
        song_info = self.song_queue.pop(0)
        self.now_playing = song_info
        await self.ctx.send(f'Now playing: **{song_info["title"]}**')
        source = discord.FFmpegPCMAudio(song_info['url'], **ffmpeg_options)
        self.ctx.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(self.song_finished(song_info), self.bot.loop))
        self.ctx.voice_client.source.volume = self.volume

    async def remove_song(self, index=None):
        """Remove song from queue, skip current song, or end playing"""
        if not self.is_playing:
            await self.ctx.send('Nothing is playing.')
            return
        if index is None:
            await self.ctx.send(f'Skipped: __**{self.now_playing["title"]}**__')
            self.ctx.voice_client.stop()
            os.remove(self.now_playing['filename'])
            if self.song_queue:
                await self.play_song()
            else:
                self.is_playing = False
                await self.ctx.voice_client.disconnect()
                await self.ctx.send('Queue is empty.')
        elif index < len(self.song_queue) + 1:
            removed = self.song_queue.pop(index - 1)
            os.remove(removed['filename'])
            await self.ctx.send(f'Removed from queue: ~~**{removed["title"]}**~~')
        else:
            await self.ctx.send('Invalid queue index.')

    async def song_finished(self, song_info):
        """Callback when a song has finished playing"""
        os.remove(song_info['filename'])
        await self.ctx.send(f'Finished playing: __**{song_info["title"]}**__')
        if self.song_queue:
            await self.play_song()
        else:
            self.is_playing = False
            await self.ctx.voice_client.disconnect()
            await self.ctx.send('Queue is empty.')


    async def get_song_info(self, url):
        """Get song information and download the file"""
        loop = asyncio.get_event_loop()
        song_info = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=True))
        filename = ytdl.prepare_filename(song_info)
        song_info['filename'] = filename
        song_info['url'] = f'{filename}'
        return song_info

    async def search_song(self, query):
        request = self.youtube.search().list(
            part='id',
            q=query,
            type='video',
            videoDefinition='high',
            maxResults=1
        )
        response = await self.bot.loop.run_in_executor(None, request.execute)
        if len(response['items']) > 0:
            video_id = response['items'][0]['id']['videoId']
            return f'https://www.youtube.com/watch?v={video_id}'
        else:
            await self.ctx.send(f'Could not find a song with name **{query}**')
            return None

    async def clear_queue(self):
        """Clears every song from the queue."""
        if not self.song_queue:
            await self.ctx.send("The queue is already empty.")
        else:
            for song in self.song_queue:
                os.remove(song['filename'])
            self.song_queue.clear()
            await self.ctx.send("The queue has been cleared.")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="-", intents=intents)
player = MusicPlayer(bot)
@bot.command()
async def play(ctx, *, url):
    """Add song to the queue and start playing if the queue is empty"""
    if not ctx.author.voice:
        await ctx.send('You are not connected to a voice channel.')
        return
    if not ctx.voice_client:
        await ctx.author.voice.channel.connect()
    player.ctx = ctx
    await player.add_song(url)

@bot.command()
async def queue(ctx):
    """Display the song queue"""
    player.ctx = ctx
    if not player.song_queue:
        await ctx.send('Queue is empty.')
        return
    queue_message = 'My Playlist:\n' 
    for i, song in enumerate(player.song_queue): 
        queue_message += f'{i+1}. **{song["title"]}**\n' 
        queue_message += ''
    queue_message = '\n>>> {}'.format(queue_message)
    await ctx.send(queue_message)

@bot.command()
async def skip(ctx, index: int = None):
    """Remove song from queue, skip current song, or end playing"""
    player.ctx = ctx
    await player.remove_song(index)

@bot.command()
async def volume(ctx, volume: float = None):
    """Set or display the volume (0-1)"""
    player.ctx = ctx
    if volume is None:
        await ctx.send(f'Current volume: {player.volume}')
    else:
        player.volume = max(0, min(1, volume))
    if player.is_playing:
        player.ctx.voice_client.source.volume = player.volume
    await ctx.send(f'Volume set to: {player.volume}')

@bot.event
async def on_voice_state_update(member, before, after):
    """Disconnect from voice channel when everyone leaves"""
    if member.bot:
        return
    if not member.guild.voice_client:
        return
    if len(member.guild.voice_client.channel.members) == 1:
        await player.clear_queue()
        await member.guild.voice_client.disconnect()

@bot.event
async def on_ready():
    """Print a message when the bot is ready"""
    print(f'Logged in as {bot.user.name} ({bot.user.id})')

TOKEN = "Your token here"

# start the event loop in the main thread
bot.run(TOKEN)
