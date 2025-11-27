import discord
from discord import app_commands
import yt_dlp as youtube_dl
import asyncio
import os

# Suppress yt-dlp noise
youtube_dl.utils.bug_reports_message = lambda *args, **kwargs: ""

ytdl_format_options = {
    "format": "bestaudio/best",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",
}

ffmpeg_options = {"options": "-vn"}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5, filename=None):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get("title")
        self.url = data.get("url")
        self.filename = filename

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()

        try:
            data = await loop.run_in_executor(
                None, lambda: ytdl.extract_info(url, download=True)
            )
        except Exception as e:
            print(f"Error extracting info for {url}: {e}")
            return None

        if not data:
            return None

        if "entries" in data:
            data = data["entries"][0]

        filename = ytdl.prepare_filename(data)
        return cls(
            discord.FFmpegPCMAudio(filename, **ffmpeg_options),
            data=data,
            filename=filename,
        )

    def cleanup(self):
        if self.filename and os.path.isfile(self.filename):
            os.remove(self.filename)
            print(f"Deleted file: {self.filename}")


song_queues = {}
now_playing = {}


async def play_next_song(interaction):
    guild = interaction.guild
    if guild is None:
        return

    guild_id = guild.id
    queue = song_queues.get(guild_id, [])

    if not queue:
        voice_client = guild.voice_client
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()
        now_playing[guild_id] = None
        return

    next_track = queue.pop(0)
    now_playing[guild_id] = next_track

    def after_playback(error):
        try:
            if next_track:
                next_track.cleanup()
        except Exception as e:
            print(f"Error cleaning up track: {e}")
        try:
            asyncio.run_coroutine_threadsafe(
                play_next_song(interaction), interaction.client.loop
            )
        except Exception as e:
            print(f"Error scheduling next song: {e}")

    guild.voice_client.play(
        next_track,
        after=after_playback,
    )
    await interaction.channel.send(f"**Now playing:** {next_track.title}")


@discord.app_commands.command(name="play", description="Play a song from YouTube")
async def play(interaction: discord.Interaction, search: str):
    await interaction.response.defer()

    if interaction.guild.voice_client is None:
        if interaction.user.voice:
            await interaction.user.voice.channel.connect()
        else:
            await interaction.followup.send("You are not connected to a voice channel.")
            return

    async with interaction.channel.typing():
        player = await YTDLSource.from_url(
            search, loop=interaction.client.loop, stream=False
        )
        if player is None:
            await interaction.followup.send(
                "There was an error processing your request."
            )
            return

        guild_id = interaction.guild.id
        queue = song_queues.setdefault(guild_id, [])
        queue.append(player)
        await interaction.followup.send(f"**Added to queue:** {player.title}")

        if not interaction.guild.voice_client.is_playing():
            await play_next_song(interaction)


@discord.app_commands.command(
    name="skip", description="Skip the currently playing song"
)
async def skip(interaction: discord.Interaction):
    await interaction.response.defer()
    if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
        interaction.guild.voice_client.stop()
        await interaction.followup.send("Skipped the current song.")
    else:
        await interaction.followup.send("No song is currently playing.")


@discord.app_commands.command(
    name="stop", description="Stop playing music and leave the voice channel"
)
async def stop(interaction: discord.Interaction):
    await interaction.response.defer()

    guild_id = interaction.guild.id
    queue = song_queues.get(guild_id, [])
    current = now_playing.get(guild_id)
    voice_client = interaction.guild.voice_client

    if not voice_client:
        await interaction.followup.send("I'm not connected to a voice channel.")
        return

    try:
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
        await voice_client.disconnect()
    except Exception as e:
        print(f"Error while stopping and disconnecting: {e}")
        await interaction.followup.send(
            "There was an error disconnecting from the voice channel."
        )
        return

    try:
        if current:
            current.cleanup()
    except Exception as e:
        print(f"Error while cleaning up current track: {e}")

    now_playing[guild_id] = None
    queue.clear()
    await interaction.followup.send(
        "Disconnected from the voice channel and cleared the queue."
    )


# Newly added commands integrated properly
@discord.app_commands.command(name="queue", description="View the song queue")
async def queue(interaction: discord.Interaction):
    await interaction.response.defer()

    guild_id = interaction.guild.id
    queue = song_queues.get(guild_id, [])
    current = now_playing.get(guild_id)

    queue_list = "\n".join([f"**{i+1}.** {song.title}" for i, song in enumerate(queue)])
    if current:
        message = (
            f"**Now playing:** {current.title}\n**Next:**\n{queue_list}"
            if queue_list
            else f"**Now playing:** {current.title}\n**Next:** No songs in queue"
        )
    else:
        message = "**Now playing:** No song is currently playing.\n**Next:** No songs in queue"
    await interaction.followup.send(message)


@discord.app_commands.command(name="remove", description="Remove a song from the queue")
async def remove(interaction: discord.Interaction, index: int):
    await interaction.response.defer()

    guild_id = interaction.guild.id
    queue = song_queues.get(guild_id, [])

    if 1 <= index <= len(queue):
        removed_song = queue.pop(index - 1)
        await interaction.followup.send(f"Removed {removed_song.title} from the queue.")
    else:
        await interaction.followup.send("Invalid index. Please provide a valid number.")


@discord.app_commands.command(
    name="pause", description="Pause the currently playing song"
)
async def pause(interaction: discord.Interaction):
    await interaction.response.defer()

    if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
        interaction.guild.voice_client.pause()
        await interaction.followup.send("Paused the current song.")
    else:
        await interaction.followup.send("No song is currently playing.")


@discord.app_commands.command(
    name="resume", description="Resume the currently paused song"
)
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
