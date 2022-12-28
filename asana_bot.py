# This is a sample Python script.
import os
import time
from datetime import date, timedelta

import discord
import schedule

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import asana
from asana.error import InvalidTokenError
from collections.abc import Callable, Iterable

from discord import TextChannel

# Note: Replace this value with your own personal access token

personal_access_token = os.environ["ASANA_KEY"]

# Construct an Asana client
client = asana.Client.access_token(personal_access_token)

# Set things up to send the name of this script to us to show that you succeeded! This is optional.
client.options['client_name'] = "hello_world_python"

# Get your user info
me = client.users.me()

# Print out your information
print("logged in to asana client as " +  me['name'])

client.projects.find_all

b6workspace = client.workspaces.find_by_id(1203279608416517)
decisions_project = client.projects.find_by_id(1203279731709143)
chores_project = client.projects.find_by_id(1203288705129613)
known_projects = [decisions_project, chores_project]
known_project_ids = list(map(lambda x: x["gid"], known_projects))

test_channel = 1054443400767741972
main_private_channel = 1025848715702980673
event_planning_channel = 1029794106257444955
decisions_channel = 1037418339674370128
friends_channel = 1036694062339731558
suggestions_channel = 1036697304201170945
worker_bae_channel = 1039584677712896110

for proj in list(client.projects.find_all(workspace=b6workspace["gid"])):
    if proj["gid"] not in known_project_ids:
        print(f"Unknown project found: {proj}")


def get_events_sync_token(resource_id):
    # The asana events api handles initializations in a weird way. In order to start listening, you need to ask without
    #   a session id, get rejected with a 412 which *includes* the sync token that you need
    try:
        list(client.events.get({"resource": resource_id}))
    except InvalidTokenError as e:
        return e.sync


print(known_project_ids)
sync_tokens = {resource_id: get_events_sync_token(resource_id) for resource_id in known_project_ids}
print(sync_tokens)


def fetch_events_for_one_resource(resource_id, sync=None):
    try:
        print(f"fetching data from {resource_id}")
        data = client.events.get({"resource": resource_id, "sync": sync})
        return data
    except InvalidTokenError as e:
        data = None
        initial_sync = e.sync
        return fetch_events_for_one_resource(resource_id, e.sync)


def get_events_from_resources(resource_ids):
    print(sync_tokens)
    for resource_id in resource_ids:
        data = fetch_events_for_one_resource(resource_id, sync_tokens[resource_id])
        sync_tokens[resource_id] = data["sync"]
        yield from data["data"]


async def on_new_tasks(event, callbacks):
    if event["type"] != "task" or \
            event["action"] != "added" or \
            event["parent"]["gid"] not in known_project_ids:
        return
    print("Found a task event!")
    print(event)

    for callback in callbacks:
        await callback(event)


async def on_new_assignee(event, callbacks: Iterable[Callable] = []):
    if event["type"] != "task" or event["action"] != "changed" or event["change"]["field"] != "assignee":
        return
    print("Found a assignee update!")
    print(event)

    for callback in callbacks:
        callback(event)


def print_assignee(event):
    print(event)
    if event['change']['new_value'] is None:
        print(f"Task {event['resource']['name']} unassigned")
    else:
        print(
            f"New assignee {event['change'].get('new_value', {}).get('name')} added to task: {event['resource']['name']}")


async def print_new(event):
    print(event)
    print(f"New task {event['resource']['name']} added to project: {event['parent']['name']}")


async def check_for_upcoming_events(channel: TextChannel):
    pass


async def process_events(new_task_callbacks: Iterable[Callable] = None,
                         new_assignee_callbacks: Iterable[Callable] = None):
    if new_assignee_callbacks is None:
        new_assignee_callbacks = []
    if new_task_callbacks is None:
        new_task_callbacks = []
    event_generator = get_events_from_resources([chores_project["gid"], decisions_project["gid"]])

    for next_event in event_generator:
        await on_new_tasks(next_event, [print_new] + new_task_callbacks)
        await on_new_assignee(next_event, [print_assignee] + new_assignee_callbacks)


async def create_new_task(name, author, assignee="infoatbay6@gmail.com", notes=None, due_date=None, project=chores_project['gid']):
    post_data= {
            'workspace': b6workspace['gid'],
            'name': name,
            'notes': f"Created automatically by {author}\n\n",
            'projects': project
        }
    if assignee:
        post_data["assignee"] = assignee  # this is a user gid or email
    if notes:
        post_data["notes"] += notes
    if due_date:
        post_data["due_on"] = due_date
    return client.tasks.create_task(post_data)


def get_task_info(gid):
    return client.tasks.get_task(gid)

def get_upcoming_tasks():
    # this would be a convenient way to do it, but search api is only available to premium accounts
    # tasks = client.tasks.search_tasks_for_workspace(
    #     workspace_gid=b6workspace['gid']
    #     params={"due_on.before": datetime.date.today() + datetime.timedelta(days=7)}
    # )
    gen = client.projects.tasks(chores_project['gid'],
                                opt_fields='name,gid,due_on,completed,notes,assignee,assignee.name,permalink_url')
    def filter_upcoming(task):
        return (not task.get('completed')) and \
               date.fromisoformat(task.get('due_on') or '2022-01-01') < date.today() + timedelta(days=7)
    return filter(filter_upcoming, gen)

name_to_email = {
    "Anarion": "trevortds3@gmail.com",
    "cattrebuchet": "ameliafineberg@gmail.com",
    "Jules (The Coven)": "funsizedfox@gmail.com",
    "Mayhem": "mmayhemstudio7@gmail.com",
    "heckinPITA": "boettcsm@gmail.com",
    "PolyOzymandias": "soongkit@gmail.com",
    "𝓞𝓹𝓪𝓵 𝓑𝓾𝓷𝓷𝔂": "hmmottinger@gmail.com",
    "LoafusCromwel": "nabrahamson@gmail.com",
    "ladydimitrescustampon": "baristasupreme@icloud.com"
}

def assign_user_to_task(name, url):
    task_gid = url.split('/')[-1]
    task = client.tasks.get_task(task_gid)
    print(f"assigning {name} to this task {task}")
    print(task)
    if name not in name_to_email:
        raise Exception(f"I don't know the email of user {name}")
    result = client.tasks.update_task(task_gid, {'assignee': name_to_email[name]}, opt_pretty=True)
    print(result)
    return result
