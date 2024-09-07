import discord
from discord import app_commands

# Intents and client setup
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True  # Required to handle member join events

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# List of cogs to load
cogs = ['cogs.music', 'cogs.welcome', 'cogs.basic']

# Guild IDs and their corresponding channel IDs where role picker messages will be sent
# Replace with your actual guild IDs and channel IDs
CHANNEL_IDS = {
    507008776482586624: 1279312642930114591,  # Guild ID for "Unforseeable Activities"
    1002171625367674910: 1280242025844838444,  # Guild ID for "Kommand0e"
}

# Emoji to role mapping
ROLE_EMOJI_MAP = {
    "🎮": ("Gamer", "Steam sale notifications")
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
    """
    Ensures that a role with the specified name and color exists in the guild.
    Creates the role if it does not exist.
    """
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
    # Synchronize the command tree with Discord
    await tree.sync()
    print(f'Logged in as {client.user}')

    # Iterate over each guild (server) the bot is in
    for guild in client.guilds:
        channel_id = CHANNEL_IDS.get(guild.id)  # Use guild ID to get the channel ID
        if not channel_id:
            print(f"No channel ID configured for guild: {guild.name} (ID: {guild.id})")
            continue

        channel = client.get_channel(channel_id)
        if channel:
            print(f"Sending messages in guild: {guild.name} (ID: {guild.id})")
            # Ensure all color roles exist
            role_mentions = {}
            for role_name, color in COLOR_EMOJI_MAP.values():
                role = await ensure_role_exists(guild, role_name, color)
                role_mentions[role_name] = role.id

            # Send color picker message with proper role mentions
            color_text = "> # Name Colors\n" + "\n".join(
                [f"> {emoji} <@&{role_mentions[role_name]}>" for emoji, (role_name, _) in COLOR_EMOJI_MAP.items()])
            color_message = await channel.send(color_text)
            # Add reactions based on the defined color emoji map
            for emoji in COLOR_EMOJI_MAP.keys():
                await color_message.add_reaction(emoji)
            print(f'Color picker sent in {guild.name}.')

            # Send role picker message
            role_text = "> # Role Selection\n" + "\n".join(
                [f"> {emoji}: {description}" for emoji, (_, description) in ROLE_EMOJI_MAP.items()])
            role_message = await channel.send(role_text)
            # Add reactions based on the defined role emoji map
            for emoji in ROLE_EMOJI_MAP.keys():
                await role_message.add_reaction(emoji)
            print(f'Role picker sent in {guild.name}.')
        else:
            print(f"Channel not found in guild: {guild.name} (ID: {guild.id})")

@client.event
async def on_reaction_add(reaction, user):
    if user.bot:  # Ignore reactions from bots
        return

    guild = reaction.message.guild
    if guild.id not in CHANNEL_IDS:
        return

    channel = client.get_channel(CHANNEL_IDS[guild.id])
    if reaction.message.channel.id != channel.id:
        return

    # Ensure only one reaction per user on the color picker message
    if reaction.emoji in COLOR_EMOJI_MAP.keys():
        # Remove all other reactions from the user except the current one
        for react in reaction.message.reactions:
            if react.emoji != reaction.emoji:
                async for reacting_user in react.users():
                    if reacting_user == user:
                        await react.remove(user)

    # Handle color role assignment
    color_role_name, color = COLOR_EMOJI_MAP.get(reaction.emoji, (None, None))
    if color_role_name:
        # Ensure the role exists before assigning
        color_role = await ensure_role_exists(guild, color_role_name, color)
        if color_role:
            await user.add_roles(color_role)  # Add the new color role
        return  # Exit early to reduce unnecessary processing

    # Handle other role assignment
    role_info = ROLE_EMOJI_MAP.get(reaction.emoji)
    if role_info:
        role_name, _ = role_info
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            await user.add_roles(role)

@client.event
async def on_reaction_remove(reaction, user):
    if user.bot:  # Ignore reactions from bots
        return

    guild = reaction.message.guild
    if guild.id not in CHANNEL_IDS:
        return

    channel = client.get_channel(CHANNEL_IDS[guild.id])
    if reaction.message.channel.id != channel.id:
        return

    # Handle color role removal
    color_role_name, _ = COLOR_EMOJI_MAP.get(reaction.emoji, (None, None))
    if color_role_name:
        color_role = discord.utils.get(guild.roles, name=color_role_name)
        if color_role:
            await user.remove_roles(color_role)

    # Handle other role removal
    role_info = ROLE_EMOJI_MAP.get(reaction.emoji)
    if role_info:
        role_name, _ = role_info
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            await user.remove_roles(role)

# Load all cogs
for cog in cogs:
    try:
        module = __import__(cog, fromlist=['setup'])
        module.setup(client, tree)  # Pass client and tree to the setup function in each cog
        print(f"Loaded cog: {cog}")
    except Exception as e:
        print(f"Failed to load cog {cog}: {e}")

# Run the client with your bot token
client.run('MTEyOTI3MDA1OTUxMzE1MTUzOQ.G1I4aa.s4-Zh5bFut1Cgx8RPBkMCeCarX6k2ws1ooNCQI')  # Replace with your actual bot token