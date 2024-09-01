import discord
from discord import app_commands
from discord.ext import commands

# Define the channel ID and the role emoji map
CHANNEL_ID = 1279312642930114591  # Replace with your actual channel ID
ROLE_EMOJI_MAP = {
    "🎮": "Gamer"  # Emoji to role mapping
}

class RolePicker(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        channel = self.client.get_channel(CHANNEL_ID)
        if channel:
            text = "# Pick your role(s)\n🎮: Steam-Sale Notifications"
            message = await channel.send(text)
            # Add reactions based on the defined emoji map
            for emoji in ROLE_EMOJI_MAP.keys():
                await message.add_reaction(emoji)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:  # Ignore reactions from bots
            return

        channel = self.client.get_channel(CHANNEL_ID)
        if reaction.message.channel.id != channel.id:
            return

        # Check if the reaction emoji is in the role map
        role_name = ROLE_EMOJI_MAP.get(reaction.emoji)
        if role_name:
            guild = reaction.message.guild
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                await user.add_roles(role)
                await reaction.message.channel.send(f"{user.mention} has been given the {role.name} role.", delete_after=5)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        if user.bot:  # Ignore reactions from bots
            return

        channel = self.client.get_channel(CHANNEL_ID)
        if reaction.message.channel.id != channel.id:
            return

        # Check if the reaction emoji is in the role map
        role_name = ROLE_EMOJI_MAP.get(reaction.emoji)
        if role_name:
            guild = reaction.message.guild
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                await user.remove_roles(role)
                await reaction.message.channel.send(f"{user.mention} has been removed from the {role.name} role.", delete_after=5)

async def setup(client, tree):
    await client.add_cog(RolePicker(client))
