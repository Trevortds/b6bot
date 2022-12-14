import json
import os
import discord
from discord import app_commands, TextChannel, Reaction, User, Interaction
from discord.ext import tasks, commands
from datetime import date

from asana_bot import process_events, check_for_upcoming_events, chores_project, decisions_project, create_new_task, \
    get_task_info, get_upcoming_tasks, assign_user_to_task

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
@app_commands.choices(assignee=[
        app_commands.Choice(name="None", value=""),
        app_commands.Choice(name="Bay Six", value="infoatbay6@gmail.com"),
        app_commands.Choice(name="Trevor", value="trevortds3@gmail.com"),
        app_commands.Choice(name="Amelia", value="ameliafineberg@gmail.com"),
        app_commands.Choice(name="Jules", value="funsizedfox@gmail.com"),
        app_commands.Choice(name="Mayhem", value="mmayhemstudio7@gmail.com"),
        app_commands.Choice(name="Sam", value="boettcsm@gmail.com"),
        app_commands.Choice(name="Kit", value="soongkit@gmail.com"),
        app_commands.Choice(name="Hale", value="hmmottinger@gmail.com"),
        app_commands.Choice(name="Noah", value="nabrahamson@gmail.com"),
        app_commands.Choice(name="Ylva", value="baristasupreme@icloud.com")
        ])
async def create_task(interaction: Interaction, name: str,  assignee: app_commands.Choice[str], due_date_y_m_d: str=date.today().isoformat(), description: str = ""):
    print(interaction)
    print(interaction.user.display_name)
    print(assignee.value)
    try:
        new_task = await create_new_task(name, author=interaction.user.display_name,  due_date=due_date_y_m_d, assignee=assignee.value, notes=description)
        print(new_task)
        await interaction.response.send_message("created task: " + new_task['permalink_url'])
    except Exception as e:
        await interaction.response.send_message("Something went wrong: " + str(e))


@tree.command(name="createdecision",
              description="Create an asana task in the decision project, and open a thread about it",
              guild=discord.Object(id=guild_id))
@app_commands.choices(owner=[
        app_commands.Choice(name="None", value=""),
        app_commands.Choice(name="Bay Six", value="infoatbay6@gmail.com"),
        app_commands.Choice(name="Trevor", value="trevortds3@gmail.com"),
        app_commands.Choice(name="Amelia", value="ameliafineberg@gmail.com"),
        app_commands.Choice(name="Jules", value="funsizedfox@gmail.com"),
        app_commands.Choice(name="Mayhem", value="mmayhemstudio7@gmail.com"),
        app_commands.Choice(name="Sam", value="boettcsm@gmail.com"),
        app_commands.Choice(name="Kit", value="soongkit@gmail.com"),
        app_commands.Choice(name="Hale", value="hmmottinger@gmail.com"),
        app_commands.Choice(name="Noah", value="nabrahamson@gmail.com"),
        app_commands.Choice(name="Ylva", value="baristasupreme@icloud.com")
        ])
async def create_decision(interaction: Interaction, name: str, description: str,  owner: app_commands.Choice[str], due_date_y_m_d: str=date.today().isoformat(),):
    print(interaction)
    print(interaction.user.name)
    print(owner.value)
    try:
        new_task = await create_new_task(name, author=interaction.user.display_name, due_date=due_date_y_m_d,
                                         assignee=owner.value, notes=description, project=decisions_project['gid'])
        print(new_task)
        await interaction.response.send_message("created decision: " + new_task['permalink_url'])
    except Exception as e:
        await interaction.response.send_message("Something went wrong: " + str(e))


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
        # self.check_upcoming_unassigned_events.start()

    def cog_unload(self) -> None:
        self.check_new_asana_events.cancel()
        self.check_upcoming_unassigned_events.cancel()

    @tasks.loop(seconds=5.0)
    async def check_new_asana_events(self):
        self.message_count += 1
        channel = self.client.get_channel(1054443400767741972)
        await process_events(new_task_callbacks=[self.announce_new_task])

    @tasks.loop(hours=24*7)
    async def check_upcoming_unassigned_events(self):
        channel = self.channel_objects["test"]
        upcoming_assigned_embeds = []
        upcoming_unassigned_embeds = []
        for task in get_upcoming_tasks():
            newEmbed = discord.Embed(title=f"{task['name']}", color=0x42f5d1)
            newEmbed.url = task['permalink_url']
            newEmbed.add_field(name="Due on", value=task.get("due_on"))
            newEmbed.add_field(name="Description", value=task.get("notes") or "No Description", inline=False)
            if task.get('assignee'):
                newEmbed.add_field(name="Assignee", value= task["assignee"]["name"])
                upcoming_assigned_embeds.append(newEmbed)
            else:
                newEmbed.color = 0xd93465
                upcoming_unassigned_embeds.append(newEmbed)

        chunked_upcoming_assigned_embeds = x = [upcoming_assigned_embeds[i:i + 10] for i in range(0, len(upcoming_assigned_embeds), 10)]
        chunked_upcoming_unassigned_embeds = x = [upcoming_unassigned_embeds[i:i + 10] for i in range(0, len(upcoming_unassigned_embeds), 10)]

        for chunk in chunked_upcoming_assigned_embeds:
            await channel.send("Upcoming tasks in the next 7 days: ", embeds=chunk)
        for chunk in chunked_upcoming_unassigned_embeds:
            await channel.send("Upcoming tasks that need volunteers: ", embeds=chunk)




    @client.event
    async def on_reaction_add(self, reaction, user):
        # this doesn't work
        print("new reaction")
        print(reaction)
        print(user)
        emoji = reaction.emoji
        if user.bot:
            return

    async def announce_new_task(self, event):
        # select channel based on which project task was created in
        if event["parent"]['gid'] == chores_project['gid']:
            channel = self.channel_objects["test"]
        else:
            channel = self.channel_objects["test"]
        # embed information
        task_info = get_task_info(event['resource']['gid'])
        print(task_info)
        embed = discord.Embed(title=f"{event['resource']['name']}", color=0x00ff00)
        embed.add_field(name='Project', value=event['parent']['name'], inline=True)
        if event.get('user'):
            embed.add_field(name='Author', value=event.get('user', {}).get('name', "Automated"))
        if task_info.get("notes"):
            embed.add_field(name="Description", value=task_info.get("notes"))
        embed.url = task_info["permalink_url"]
        message = await channel.send(event['resource']['name'], embed=embed)
        # add volunteer reaction
        await message.add_reaction("????")
        # make discussion thread for new decisions
        if event["parent"]['gid'] == decisions_project['gid']:
            thread = await message.create_thread(name=event['resource']['name'])
            await thread.send("Conversation goes here")


@client.event
async def on_reaction_add(reaction: Reaction, user: User):
    # this works now
    print("new reaction client")
    print(reaction)
    emoji = reaction.emoji
    print(emoji)
    if user.bot:
        return

    print("following user wants to volunteer")
    print(user.display_name)
    print(user.name)
    print(user)
    print(reaction.message.embeds)
    embed = reaction.message.embeds[0]
    print(embed)
    print(embed.url)
    try:
        result = assign_user_to_task(user.name, embed.url)
        embed.add_field(name="Volunteer", value=user.display_name, inline=False)
        await reaction.message.edit(embeds=[embed])
    except Exception as e:
        await reaction.message.channel.send("Failed to self-assign: " + str(e))






'''
notes:
to have discord add reactions to messages, use discord.Message.add_reaction(":emoji:")
to have it listen for reactions, use the function 
@bot.event
async def on_reaction_add(reaction, user)

To make formatted messages, use embeds. eg
@bot.command()
async def bug(ctx, desc=None, rep=None):
    user = ctx.author
    await ctx.author.send('```Please explain the bug```')
    responseDesc = await bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout=300)
    description = responseDesc.content
    await ctx.author.send('````Please provide pictures/videos of this bug```')
    responseRep = await bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout=300)
    replicate = responseRep.content
    embed = discord.Embed(title='Bug Report', color=0x00ff00)
    embed.add_field(name='Description', value=description, inline=False)
    embed.add_field(name='Replicate', value=replicate, inline=True)
    embed.add_field(name='Reported By', value=user, inline=True)
    adminBug = bot.get_channel(733721953134837861)
    await adminBug.send(embed=embed)
    # Add 3 reaction (different emojis) here
'''

client.run(bot_token)

# bot = commands.Bot
# bot.add_cog(AsanaWatcher(bot))


