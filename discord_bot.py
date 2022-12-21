import os
import discord
from discord import app_commands
from discord.ext import tasks, commands

from asana_bot import process_events

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


guild_id = os.environ["GUILD_ID"]
bot_token = os.environ["DISCORD_TOKEN"]

test_channel = 1054443400767741972
main_private_channel = 1025848715702980673
event_planning_channel = 1029794106257444955
decisions_channel = 1037418339674370128
friends_channel = 1036694062339731558
suggestions_channel = 1036697304201170945
worker_bae_channel = 1039584677712896110


@tree.command(name="createtask", description="Create an asana task in the General project",
              guild=discord.Object(id=guild_id))
async def create_task(interaction):
    await interaction.response.send_message("Not implemented yet, sorry!")


@tree.command(name="createdecision",
              description="Create an asana task in the decision project, and open a thread about it",
              guild=discord.Object(id=guild_id))
async def create_task(interaction):
    await interaction.response.send_message("Not implemented yet, sorry!")


@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=guild_id))
    bot = commands.Bot
    await bot.add_cog(AsanaWatcher(bot))

    print("Ready!")

class AsanaWatcher(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = client
        self.channel_objects = {
            "test": self.client.get_channel(test_channel),
            "main-private": self.client.get_channel(main_private_channel),
            "event-planning": self.client.get_channel(event_planning_channel),
            "decisions": self.client.get_channel(decisions_channel),
            "friends": self.client.get_channel(friends_channel),
            "suggestions": self.client.get_channel(suggestions_channel),
            "worker-baes": self.client.get_channel(worker_bae_channel)
        }
        self.data = []
        self.message_count = 0
        self.check_new_asana_events.start()

    def cog_unload(self) -> None:
        self.check_new_asana_events.cancel()

    @tasks.loop(seconds=5.0)
    async def check_new_asana_events(self):
        self.message_count += 1
        channel = self.client.get_channel(1054443400767741972)
        process_events(self.channel_objects)
        await channel.send(f"channel send test {self.message_count}")


client.run(bot_token)

# bot = commands.Bot
# bot.add_cog(AsanaWatcher(bot))


