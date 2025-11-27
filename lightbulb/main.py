import asyncio
import discord
from discord import app_commands
import os

TOKEN = os.getenv("LIGHTBULB_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("LIGHTBULB_BOT_TOKEN environment variable is not set")

# Intents and client setup
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.voice_states = True
intents.members = True  # Required to handle member join events

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# List of cogs to load
cogs = ["cogs.music", "cogs.welcome", "cogs.basic"]


# Guild IDs and their corresponding channel IDs where role picker messages will be sent
class Server:
    def __init__(self, name: str, id: int, channel: int = 0):
        self.name = name
        self.id = id
        self.channel = channel


GUILDS = [
    Server("Unforseeable Activities", 507008776482586624, 1279312642930114591),
    Server("Kommand0e", 1301398304839438356, 1301399496030294036),
]

# Helper set for quick guild lookup
GUILD_IDS = {server.id for server in GUILDS}

# Emoji to role mapping
ROLE_EMOJI_MAP = {
    "🎮": ("Gamer", "Free Steam games"),
    "💎": ("Co-op warrior", "Server info"),
    "💿": ("DJ", "Access to song requests"),
    "🏎️": ("RL", "Rocket League stats"),
}

# Color picker emoji to role map with corresponding colors (RGB format)
COLOR_EMOJI_MAP = {
    "🔴": ("Red", discord.Color.red()),
    "🟠": ("Orange", discord.Color.orange()),
    "🟡": ("Yellow", discord.Color.gold()),
    "🟢": ("Green", discord.Color.green()),
    "🔵": ("Blue", discord.Color.blue()),
    "🟣": ("Purple", discord.Color.purple()),
    "🟤": ("Brown", discord.Color.from_str("#8f653b")),
    "⚫": ("Black", discord.Color.from_rgb(28, 28, 28)),  # Using default for black
    "⚪": ("White", discord.Color.from_rgb(255, 255, 255)),  # Custom white color
}


async def ensure_role_exists(guild, role_name, color):
    role = discord.utils.get(guild.roles, name=role_name)
    if not role:
        try:
            role = await guild.create_role(
                name=role_name, color=color, reason="Color role created by bot"
            )
            print(f"Created role: {role_name} with color {color}")
        except discord.Forbidden:
            print(f"Missing permissions to create the role: {role_name}")
        except Exception as e:
            print(f"Error creating role {role_name}: {e}")
    return role


@client.event
async def on_ready():
    # Sync commands for each configured guild
    for server in GUILDS:
        try:
            guild = discord.Object(id=server.id)
            await tree.sync(guild=guild)
            print(f"Synced commands for guild: {server.name} ({server.id})")
        except Exception as e:
            print(
                f"Failed to sync commands for guild: {server.name} ({server.id}) - {e}"
            )

    # Global sync fallback in case guild-specific sync fails
    try:
        await tree.sync()
        print("Globally synced commands.")
    except Exception as e:
        print(f"Failed to globally sync commands - {e}")

    print(f"Logged in as {client.user}")

    # Process messages in each configured guild for role and color pickers
    for server in GUILDS:
        guild = client.get_guild(server.id)
        if not guild:
            print(f"Bot is not in guild: {server.name} (ID: {server.id})")
            continue

        channel = client.get_channel(server.channel)
        if channel:
            print(f"Processing messages in guild: {server.name} (ID: {server.id})")
            messages = [message async for message in channel.history(limit=2)]

            # Prepare role and color picker texts
            role_mentions = {}
            for role_name, color in COLOR_EMOJI_MAP.values():
                role = await ensure_role_exists(guild, role_name, color)
                role_mentions[role_name] = role.id

            color_text = "> # Name Colors\n" + "\n".join(
                [
                    f"> {emoji} <@&{role_mentions[role_name]}>"
                    for emoji, (role_name, _) in COLOR_EMOJI_MAP.items()
                ]
            )
            role_text = "> # Role Selection\n" + "\n".join(
                [
                    f"> {emoji} for **{description}**"
                    for emoji, (_, description) in ROLE_EMOJI_MAP.items()
                ]
            )

            if len(messages) >= 2:
                # Identify which message to edit based on specific text patterns
                for message in messages:
                    if "Name Colors" in message.content:
                        await message.edit(content=color_text)
                        if len(message.reactions) < len(COLOR_EMOJI_MAP.keys()):
                            print("New color added!")
                            reacted_emojis = [
                                reaction.emoji for reaction in message.reactions
                            ]
                            for emoji in COLOR_EMOJI_MAP.keys():
                                if emoji not in reacted_emojis:
                                    await message.add_reaction(emoji)
                    elif "Role Selection" in message.content:
                        await message.edit(content=role_text)
                        if len(message.reactions) < len(ROLE_EMOJI_MAP.keys()):
                            print("New role added!")
                            reacted_emojis = [
                                reaction.emoji for reaction in message.reactions
                            ]
                            for emoji in ROLE_EMOJI_MAP.keys():
                                if emoji not in reacted_emojis:
                                    await message.add_reaction(emoji)
                print(f"Updated color and role picker messages in {server.name}.")
            else:
                # Send new messages if not found
                color_message = await channel.send(color_text)
                for emoji in COLOR_EMOJI_MAP.keys():
                    await color_message.add_reaction(emoji)
                role_message = await channel.send(role_text)
                for emoji in ROLE_EMOJI_MAP.keys():
                    await role_message.add_reaction(emoji)
                print(f"Sent new color and role picker messages in {server.name}.")
        else:
            print(f"Channel not found in guild: {server.name} (ID: {server.id})")


@client.event
async def on_raw_reaction_add(payload):
    if payload.guild_id is None:  # Ignore DMs
        return

    guild = client.get_guild(payload.guild_id)
    # Only process if the guild is one of the configured ones
    if guild.id not in GUILD_IDS:
        return

    channel = client.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    user = guild.get_member(payload.user_id)

    if user.bot:
        return

    # For color picker reactions, ensure only one reaction per user
    if payload.emoji.name in COLOR_EMOJI_MAP.keys():
        for react in message.reactions:
            if str(react.emoji) != str(payload.emoji):
                async for reacting_user in react.users():
                    if reacting_user == user:
                        try:
                            await react.remove(user)
                            await asyncio.sleep(0.1)
                        except discord.Forbidden:
                            print("Bot does not have permission to remove reactions.")
                        except discord.HTTPException as e:
                            print(f"Rate limit hit while removing reaction: {e}")
                            await asyncio.sleep(1)
                        except Exception as e:
                            print(f"Error removing reaction: {e}")

    # Handle color role assignment based on emoji
    color_role_name, color = COLOR_EMOJI_MAP.get(payload.emoji.name, (None, None))
    if color_role_name:
        color_role = await ensure_role_exists(guild, color_role_name, color)
        if color_role:
            await user.add_roles(color_role)
        return

    # Handle other role assignments
    role_info = ROLE_EMOJI_MAP.get(payload.emoji.name)
    if role_info:
        role_name, _ = role_info
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            await user.add_roles(role)


@client.event
async def on_raw_reaction_remove(payload):
    if payload.guild_id is None:
        return

    guild = client.get_guild(payload.guild_id)
    if guild.id not in GUILD_IDS:
        return

    channel = client.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    user = guild.get_member(payload.user_id)
    if user is None:
        return

    # Handle removal for color roles
    color_role_name, _ = COLOR_EMOJI_MAP.get(payload.emoji.name, (None, None))
    if color_role_name:
        color_role = discord.utils.get(guild.roles, name=color_role_name)
        if color_role:
            await user.remove_roles(color_role)

    # Handle removal for other roles
    role_info = ROLE_EMOJI_MAP.get(payload.emoji.name)
    if role_info:
        role_name, _ = role_info
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            await user.remove_roles(role)


# Load all cogs
for cog in cogs:
    try:
        module = __import__(cog, fromlist=["setup"])
        module.setup(client, tree)
        print(f"Loaded cog: {cog}")
    except Exception as e:
        print(f"Failed to load cog {cog}: {e}")

# Run the client with your bot token
client.run(TOKEN)  # Replace with your actual bot token
