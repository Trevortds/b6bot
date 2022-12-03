import os

import discord
from discord import app_commands

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

guild_id = os.environ["GUILD_ID"]
bot_token = os.environ["DISCORD_TOKEN"]

@tree.command(name = "commandname", description = "My first application Command", guild=discord.Object(id=guild_id)) #Add the guild ids in which the slash command will appear. If it should be in all, remove the argument, but note that it will take some time (up to an hour) to register the command if it's for all guilds.
async def first_command(interaction):
    await interaction.response.send_message("Hello!")

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=guild_id))
    print("Ready!")

client.run(bot_token)