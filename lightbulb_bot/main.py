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
cogs = ['cogs.music', 'cogs.welcome', 'cogs.basic', 'cogs.imagine', 'cogs.rolepicker']

# Channel ID where the role picker message will be sent
CHANNEL_ID = 1279312642930114591  # Replace with your actual channel ID

# Discord bot token
TOKEN = 'MTEyOTI3MDA1OTUxMzE1MTUzOQ.Gewhaj.3y6kxshPbRdcrPB2pa5AsxxfoyYHUmgApKpGMo'  # Replace with your actual bot token

@client.event
async def on_ready():
    # Synchronize the command tree with Discord
    await tree.sync()
    print(f'Logged in as {client.user}')

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
