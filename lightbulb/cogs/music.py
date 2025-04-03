import discord
from discord import app_commands
import yt_dlp as youtube_dl
import asyncio
import os

# Suppress yt-dlp noise
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
    def __init__(self, source, *, data, volume=0.5, filename=None):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.filename = filename

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=True))
        if 'entries' in data:
            data = data['entries'][0]

        filename = ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data, filename=filename)
    
    def cleanup(self):
        if self.filename and os.path.isfile(self.filename):
            os.remove(self.filename)
            print(f"Deleted file: {self.filename}")

song_queue = []
now_playing = None

async def play_next_song(interaction):
    global now_playing
    if song_queue:
        now_playing = song_queue.pop(0)
        interaction.guild.voice_client.play(now_playing, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(interaction), interaction.client.loop))
        await interaction.channel.send(f'**Now playing:** {now_playing.title}')
    else:
        await interaction.guild.voice_client.disconnect()
        now_playing = None

    if now_playing:
        now_playing.cleanup()

@discord.app_commands.command(name='play', description='Play a song from YouTube')
async def play(interaction: discord.Interaction, search: str):
    await interaction.response.defer()
    
    if interaction.guild.voice_client is None:
        if interaction.user.voice:
            await interaction.user.voice.channel.connect()
        else:
            await interaction.followup.send("You are not connected to a voice channel.")
            return

    async with interaction.channel.typing():
        player = await YTDLSource.from_url(search, loop=interaction.client.loop, stream=False)
        if player is None:
            await interaction.followup.send("There was an error processing your request.")
            return

        song_queue.append(player)
        await interaction.followup.send(f'**Added to queue:** {player.title}')

        if not interaction.guild.voice_client.is_playing():
            await play_next_song(interaction)

@discord.app_commands.command(name='skip', description='Skip the currently playing song')
async def skip(interaction: discord.Interaction):
    await interaction.response.defer()
    if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
        interaction.guild.voice_client.stop()
        await interaction.followup.send("Skipped the current song.")
    else:
        await interaction.followup.send("No song is currently playing.")

@discord.app_commands.command(name='stop', description='Stop playing music and leave the voice channel')
async def stop(interaction: discord.Interaction):
    await interaction.response.defer()
    if interaction.guild.voice_client:
        interaction.guild.voice_client.stop()
        await interaction.guild.voice_client.disconnect()
        try:
            now_playing.cleanup() 
        except:
            pass    
        now_playing = None
        await interaction.followup.send("Disconnected from the voice channel.")
    else:
        await interaction.followup.send("I'm not connected to a voice channel.")

# Newly added commands integrated properly
@discord.app_commands.command(name='queue', description='View the song queue')
async def queue(interaction: discord.Interaction):
    await interaction.response.defer()
    
    queue_list = "\n".join([f"**{i+1}.** {song.title}" for i, song in enumerate(song_queue)])
    if now_playing:
        message = f"**Now playing:** {now_playing.title}\n**Next:**\n{queue_list}" if queue_list else f"**Now playing:** {now_playing.title}\n**Next:** No songs in queue"
    else:
        message = f"**Now playing:** No song is currently playing.\n*Next:** No songs in queue"
    await interaction.followup.send(message)

@discord.app_commands.command(name='remove', description='Remove a song from the queue')
async def remove(interaction: discord.Interaction, index: int):
    await interaction.response.defer()
    
    if 1 <= index <= len(song_queue):
        removed_song = song_queue.pop(index - 1)
        await interaction.followup.send(f'Removed {removed_song.title} from the queue.')
    else:
        await interaction.followup.send("Invalid index. Please provide a valid number.")

@discord.app_commands.command(name='pause', description='Pause the currently playing song')
async def pause(interaction: discord.Interaction):
    await interaction.response.defer()
    
    if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
        interaction.guild.voice_client.pause()
        await interaction.followup.send("Paused the current song.")
    else:
        await interaction.followup.send("No song is currently playing.")

@discord.app_commands.command(name='resume', description='Resume the currently paused song')
async def resume(interaction: discord.Interaction):
    await interaction.response.defer()
    
    if interaction.guild.voice_client and interaction.guild.voice_client.is_paused():
        interaction.guild.voice_client.resume()
        await interaction.followup.send("Resumed the current song.")
    else:
        await interaction.followup.send("No song is currently paused.")

def setup(client, tree):
    # Add all commands to the command tree
    tree.add_command(play)
    tree.add_command(skip)
    tree.add_command(stop)
    tree.add_command(queue)
    tree.add_command(remove)
    tree.add_command(pause)
    tree.add_command(resume)
