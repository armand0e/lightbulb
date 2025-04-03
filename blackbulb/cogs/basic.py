import discord
from discord import app_commands

@discord.app_commands.command(name='ding', description='Just a ding command')
async def ding(interaction: discord.Interaction):
    latency = round(interaction.client.latency * 1000)
    await interaction.response.send_message(f'Dong! Latency is {latency}ms')

def setup(client, tree):
    # Add the ding command to the command tree
    tree.add_command(ding)
