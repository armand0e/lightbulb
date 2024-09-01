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

# Channel ID where the role picker message will be sent
CHANNEL_ID = 1279312642930114591  # Replace with your actual channel ID
ROLE_EMOJI_MAP = {
    "🎮": "Gamer"  # Emoji to role mapping
}

# Color picker emoji to role map with corresponding colors (RGB format)
COLOR_EMOJI_MAP = {
    "🔴": ("Red", discord.Color.red()),
    "🟠": ("Orange", discord.Color.orange()),
    "🟡": ("Yellow", discord.Color.gold()),
    "🟢": ("Green", discord.Color.green()),
    "🔵": ("Blue", discord.Color.blue()),
    "🟣": ("Purple", discord.Color.purple()),
    "⚫": ("Black", discord.Color.default()),  # Using default for black
    "⚪": ("White", discord.Color.from_rgb(255, 255, 255)),  # Custom white color
    # Add more colors and roles as needed
}

# Discord bot token
TOKEN = 'MTEyOTI3MDA1OTUxMzE1MTUzOQ.Gewhaj.3y6kxshPbRdcrPB2pa5AsxxfoyYHUmgApKpGMo'  # Replace with your actual bot token

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

    # Ensure all color roles exist
    guild = discord.utils.get(client.guilds)  # Modify this if you want to ensure for a specific guild
    if guild:
        for role_name, color in COLOR_EMOJI_MAP.values():
            await ensure_role_exists(guild, role_name, color)

    # Send color picker message before the role picker message
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        color_text = "**Choose your name color**\nReact to select a color:"
        color_message = await channel.send(color_text)
        # Add reactions based on the defined color emoji map
        for emoji in COLOR_EMOJI_MAP.keys():
            await color_message.add_reaction(emoji)
        print(f'Color picker sent.')

        # Send role picker message
        role_text = "# Pick your role(s)\n🎮: Steam-Sale Notifications"
        role_message = await channel.send(role_text)
        # Add reactions based on the defined role emoji map
        for emoji in ROLE_EMOJI_MAP.keys():
            await role_message.add_reaction(emoji)
        print(f'Role picker sent.')

@client.event
async def on_reaction_add(reaction, user):
    if user.bot:  # Ignore reactions from bots
        return

    channel = client.get_channel(CHANNEL_ID)
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

    guild = reaction.message.guild

    # Handle color role assignment
    color_role_name, color = COLOR_EMOJI_MAP.get(reaction.emoji, (None, None))
    if color_role_name:
        # Ensure the role exists before assigning
        color_role = await ensure_role_exists(guild, color_role_name, color)
        if color_role:
            await user.add_roles(color_role)       # Add the new color role
        return  # Exit early to reduce unnecessary processing

    # Handle other role assignment
    role_name = ROLE_EMOJI_MAP.get(reaction.emoji)
    if role_name:
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            await user.add_roles(role)

@client.event
async def on_reaction_remove(reaction, user):
    if user.bot:  # Ignore reactions from bots
        return

    channel = client.get_channel(CHANNEL_ID)
    if reaction.message.channel.id != channel.id:
        return

    guild = reaction.message.guild

    # Handle color role removal
    color_role_name, _ = COLOR_EMOJI_MAP.get(reaction.emoji, (None, None))
    if color_role_name:
        color_role = discord.utils.get(guild.roles, name=color_role_name)
        if color_role:
            await user.remove_roles(color_role)

    # Handle other role removal
    role_name = ROLE_EMOJI_MAP.get(reaction.emoji)
    if role_name:
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
client.run(TOKEN)
