import asyncio
import discord
from discord import app_commands

# Intents and client setup
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.voice_states = True
intents.members = True  # Required to handle member join events

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# List of cogs to load
cogs = ['cogs.music', 'cogs.welcome', 'cogs.basic']

# Guild IDs and their corresponding channel IDs where role picker messages will be sent
CHANNEL_IDS = {
    507008776482586624: 1279312642930114591,  # Guild ID for "Unforseeable Activities" : Channel ID for Role Selection
    1301398304839438356: 1301399496030294036  # Guild ID for "Kommand0e" : Channel ID for Role Selection
}

# Emoji to role mapping
ROLE_EMOJI_MAP = {
    "🎮": ("Gamer", "Free Steam games"),
    "💎": ("Co-op warrior", "Server info"),
    "💿": ("DJ", "Access to song requests"),
    "🏎️": ("RL", "Rocket League stats")
}

# Color picker emoji to role map with corresponding colors (RGB format)
COLOR_EMOJI_MAP = {
    "🔴": ("Red", discord.Color.red()),
    "🟠": ("Orange", discord.Color.orange()),
    "🟡": ("Yellow", discord.Color.gold()),
    "🟢": ("Green", discord.Color.green()),
    "🔵": ("Blue", discord.Color.blue()),
    "🟣": ("Purple", discord.Color.purple()),
    "🟤": ("Brown", discord.Color.from_str('#8f653b')),
    "⚫": ("Black", discord.Color.from_rgb(28, 28, 28)),  # Using default for black
    "⚪": ("White", discord.Color.from_rgb(255, 255, 255)),  # Custom white color
}

async def ensure_role_exists(guild, role_name, color):
    role = discord.utils.get(guild.roles, name=role_name)
    if not role:
        try:
            role = await guild.create_role(name=role_name, color=color, reason="Color role created by bot")
            print(f"Created role: {role_name} with color {color}")
        except discord.Forbidden:
            print(f"Missing permissions to create the role: {role_name}")
        except Exception as e:
            print(f"Error creating role {role_name}: {e}")
    return role

@client.event
async def on_ready():
    for guild_id in CHANNEL_IDS.keys():
        guild = discord.Object(id=guild_id)
        await tree.sync(guild=guild)  # Sync commands for specific guild
        print(f'Synced commands for guild: {guild_id}')
    print(f'Logged in as {client.user}')

    for guild in client.guilds:
        channel_id = CHANNEL_IDS.get(guild.id)
        if not channel_id:
            print(f"No channel ID configured for guild: {guild.name} (ID: {guild.id})")
            continue

        channel = client.get_channel(channel_id)
        if channel:
            print(f"Processing messages in guild: {guild.name} (ID: {guild.id})")

            # Fetch the first two messages in the channel
            messages = [message async for message in channel.history(limit=2)]

            # Prepare role and color picker text
            role_mentions = {}
            for role_name, color in COLOR_EMOJI_MAP.values():
                role = await ensure_role_exists(guild, role_name, color)
                role_mentions[role_name] = role.id

            color_text = "> # Name Colors\n" + "\n".join(
                [f"> {emoji} <@&{role_mentions[role_name]}>" for emoji, (role_name, _) in COLOR_EMOJI_MAP.items()])
            role_text = "> # Role Selection\n" + "\n".join(
                [f"> {emoji} for **{description}**" for emoji, (_, description) in ROLE_EMOJI_MAP.items()])

            if len(messages) >= 2:
                # Identifying which message to edit based on specific text patterns
                for message in messages:
                    if "Name Colors" in message.content:
                        await message.edit(content=color_text)
                        if len(message.reactions) < len(COLOR_EMOJI_MAP.keys()):
                            print("New color added!")
                            reacted_emojis = []
                            for reaction in message.reactions:
                                reacted_emojis.append(reaction.emoji)
                            for emoji in COLOR_EMOJI_MAP.keys():
                                if emoji in reacted_emojis:
                                    pass
                                else:
                                    await message.add_reaction(emoji)
                    elif "Role Selection" in message.content:
                        await message.edit(content=role_text)
                        if len(message.reactions) < len(ROLE_EMOJI_MAP.keys()):
                            print("New role added!")
                            reacted_emojis = []
                            for reaction in message.reactions:
                                reacted_emojis.append(reaction.emoji)
                            for emoji in ROLE_EMOJI_MAP.keys():
                                if emoji in reacted_emojis:
                                    pass
                                else:
                                    await message.add_reaction(emoji)
                                    
                                    
                print(f'Updated color and role picker messages in {guild.name}.')
            else:
                # Send new messages if not found
                color_message = await channel.send(color_text)
                for emoji in COLOR_EMOJI_MAP.keys():
                    await color_message.add_reaction(emoji)

                role_message = await channel.send(role_text)
                for emoji in ROLE_EMOJI_MAP.keys():
                    await role_message.add_reaction(emoji)
                print(f'Sent new color and role picker messages in {guild.name}.')
        else:
            print(f"Channel not found in guild: {guild.name} (ID: {guild.id})")

@client.event
async def on_raw_reaction_add(payload):
    if payload.guild_id is None:  # Ignore DMs
        return

    guild = client.get_guild(payload.guild_id)
    if guild.id not in CHANNEL_IDS:
        return

    channel = client.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    user = guild.get_member(payload.user_id)

    # Ensure that the bot and user are in the right context
    if user.bot:
        return

    # Ensure only one reaction per user on the color picker message
    if payload.emoji.name in COLOR_EMOJI_MAP.keys():
        # Attempt to remove other reactions in a rate-limit-friendly way
        for react in message.reactions:
            # Use str() to compare emojis as string representations for consistency
            if str(react.emoji) != str(payload.emoji):
                async for reacting_user in react.users():
                    if reacting_user == user:
                        try:
                            await react.remove(user)  # Attempt to remove the previous reaction
                            await asyncio.sleep(0.1)  # Small delay to reduce rate limit hits
                        except discord.Forbidden:
                            print("Bot does not have permission to remove reactions.")
                        except discord.HTTPException as e:
                            print(f"Rate limit hit while removing reaction: {e}")
                            await asyncio.sleep(1)  # Add delay on hitting rate limit
                        except Exception as e:
                            print(f"Error removing reaction: {e}")

    # Handle color role assignment based on emoji
    color_role_name, color = COLOR_EMOJI_MAP.get(payload.emoji.name, (None, None))
    if color_role_name:
        color_role = await ensure_role_exists(guild, color_role_name, color)
        if color_role:
            await user.add_roles(color_role)
        return

    # Handle other roles
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
    if guild.id not in CHANNEL_IDS:
        return

    channel = client.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    user = guild.get_member(payload.user_id)

    # Ensure the user is valid and the context is correct
    if user is None:
        return

    # Handle color role removal
    color_role_name, _ = COLOR_EMOJI_MAP.get(payload.emoji.name, (None, None))
    if color_role_name:
        color_role = discord.utils.get(guild.roles, name=color_role_name)
        if color_role:
            await user.remove_roles(color_role)

    # Handle other role removal
    role_info = ROLE_EMOJI_MAP.get(payload.emoji.name)
    if role_info:
        role_name, _ = role_info
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            await user.remove_roles(role)

# Load all cogs
for cog in cogs:
    try:
        module = __import__(cog, fromlist=['setup'])
        module.setup(client, tree)
        print(f"Loaded cog: {cog}")
    except Exception as e:
        print(f"Failed to load cog {cog}: {e}")

# Run the client with your bot token
client.run('MTEyOTI2NjcyNzAyNTM4NTU1NQ.Gq0tMM.VfkwGdi30mnCJZPivYtmMs8lcD2MLlLq1uC-hY')  # Replace with your actual bot token