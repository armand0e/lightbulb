import discord
from discord import app_commands
import yt_dlp as youtube_dl
import asyncio
import os
from easy_pil import Font, Editor, load_image_async

# Intents and client setup
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True  # Required to handle member join events
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Suppress noise from yt-dlp
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
        self.filename = filename  # Keep track of the filename

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=True))
        
        if 'entries' in data:
            data = data['entries'][0]

        filename = ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data, filename=filename)
    
    async def cleanup(self):
        """Delete the downloaded file."""
        if self.filename and os.path.isfile(self.filename):
            await os.remove(self.filename)
            print(f"Deleted file: {self.filename}")

song_queue = []
now_playing = None

@client.event
async def on_ready():
    await tree.sync()
    print(f'Logged in as {client.user}')

async def play_next_song(interaction):
    global now_playing
    if song_queue:
        now_playing = song_queue.pop(0)
        interaction.guild.voice_client.play(now_playing, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(interaction), client.loop))
        await interaction.channel.send(f'**Now playing:** {now_playing.title}')
    else:
        await interaction.guild.voice_client.disconnect()
        now_playing = None
    
    # Clean up the file after playing
    if now_playing:
        now_playing.cleanup()

# New member welcome message event
@client.event
async def on_member_join(member):
    channel = member.guild.system_channel  # Use system channel if available
    if channel is not None:
        # Mention #general channel by its ID
        general_channel = discord.utils.get(member.guild.text_channels, name="general")
        general_channel_mention = f"<#{general_channel.id}>" if general_channel else "#general"
        # Send the welcome message with the image
        await channel.send(f"Hey {member.mention} Welcome to {member.guild.name}! Make sure to check out: {general_channel_mention} We hope you enjoy your stay here. :purple_heart:")
        # Load the image using `load_image_async` method
        image = await load_image_async(member.display_avatar.url)
        # Initialize the profile and pass image as a parameter
        profile = Editor(image).resize((150, 150)).circle_image()
        # Initialize the background and pass profile as a parameter
        background = Editor("banner.png")
        
        # Fonts
        poppins = Font.poppins(size=50, variant="bold")
        poppins_small = Font.poppins(size=25, variant="regular")
        poppins_light = Font.poppins(size=20, variant="light")

        background.paste(profile, (325, 90))
        background.ellipse((325, 90), 150, 150, outline="white", stroke_width=4)
        background.text(
            (400, 260),
            "WELCOME",
            color="white",
            font=poppins,
            align="center",
            stroke_width=2,
        )
        background.text(
            (400, 325),
            f"{member.name}",
            color="white",
            font=poppins_small,
            align="center",
        )
        background.text(
            (400, 360),
            f"You are the {member.guild.member_count + 1}th Member",
            color="#0BE7F5",
            font=poppins_small,
            align="center",
        )
        # Creating nextcord.File object from image_bytes from editor
        file = discord.File(fp=background.image_bytes, filename=f'{member.name}.png')
        
        await channel.send(file=file)
            
@tree.command(name='play', description='Play a song from YouTube')
async def play(interaction: discord.Interaction, search: str):
    await interaction.response.defer()
    
    if interaction.guild.voice_client is None:
        if interaction.user.voice:
            await interaction.user.voice.channel.connect()
        else:
            await interaction.followup.send("You are not connected to a voice channel.")
            return

    async with interaction.channel.typing():
        player = await YTDLSource.from_url(search, loop=client.loop, stream=False)  # Download the file
        if player is None:
            await interaction.followup.send("There was an error processing your request.")
            return

        song_queue.append(player)
        await interaction.followup.send(f'**Added to queue:** {player.title}')

        if not interaction.guild.voice_client.is_playing():
            await play_next_song(interaction)

@tree.command(name='skip', description='Skip the currently playing song')
async def skip(interaction: discord.Interaction):
    await interaction.response.defer()
    
    if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
        interaction.guild.voice_client.stop()
        await interaction.followup.send("Skipped the current song.")
    else:
        await interaction.followup.send("No song is currently playing.")

@tree.command(name='stop', description='Stop playing music and leave the voice channel')
async def stop(interaction: discord.Interaction):
    await interaction.response.defer()
    if interaction.guild.voice_client:
        interaction.guild.voice_client.stop()  # Stop any playing song
        await interaction.guild.voice_client.disconnect()
        # Clean up the file of the currently playing song
        try:
            now_playing.cleanup() 
        except:
            pass    
        now_playing = None
        await interaction.followup.send("Disconnected from the voice channel.")
    else:
        await interaction.followup.send("I'm not connected to a voice channel.")

@tree.command(name='queue', description='View the song queue')
async def queue(interaction: discord.Interaction):
    await interaction.response.defer()
    
    queue_list = "\n".join([f"*{i+1}.* {song.title}" for i, song in enumerate(song_queue)])
    if now_playing:
        message = f"**Now playing:** {now_playing.title}\n**Queue:**\n{queue_list}" if queue_list else f"**Now playing:** {now_playing.title}\n**Queue:** No songs in queue"
    else:
        message = f"**Now playing:** No song is currently playing.\n**Queue:** No songs in queue"
    await interaction.followup.send(message)

@tree.command(name='remove', description='Remove a song from the queue')
async def remove(interaction: discord.Interaction, index: int):
    await interaction.response.defer()
    
    if 1 <= index <= len(song_queue):
        removed_song = song_queue.pop(index - 1)
        await interaction.followup.send(f'Removed {removed_song.title} from the queue.')
    else:
        await interaction.followup.send("Invalid index. Please provide a valid number.")

@tree.command(name='pause', description='Pause the currently playing song')
async def pause(interaction: discord.Interaction):
    await interaction.response.defer()
    
    if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
        interaction.guild.voice_client.pause()
        await interaction.followup.send("Paused the current song.")
    else:
        await interaction.followup.send("No song is currently playing.")

@tree.command(name='resume', description='Resume the currently paused song')
async def resume(interaction: discord.Interaction):
    await interaction.response.defer()
    
    if interaction.guild.voice_client and interaction.guild.voice_client.is_paused():
        interaction.guild.voice_client.resume()
        await interaction.followup.send("Resumed the current song.")
    else:
        await interaction.followup.send("No song is currently paused.")

@tree.command(name='ding', description='Just a ding command')
async def ding(interaction: discord.Interaction):
    latency = round(client.latency * 1000)
    await interaction.response.send_message(f'Dong! Latency is {latency}ms')

client.run('MTEyOTI3MDA1OTUxMzE1MTUzOQ.Gewhaj.3y6kxshPbRdcrPB2pa5AsxxfoyYHUmgApKpGMo')
