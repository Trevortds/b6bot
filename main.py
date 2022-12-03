# This is a sample Python script.
import time
import schedule

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import asana
from asana.error import InvalidTokenError
from collections.abc import Callable, Iterable

# Note: Replace this value with your own personal access token

personal_access_token = "1/1203279610340333:fc6e02caf8fb172a3232b3d588034ed8"

# Construct an Asana client
client = asana.Client.access_token(personal_access_token)

# Set things up to send the name of this script to us to show that you succeeded! This is optional.
client.options['client_name'] = "hello_world_python"

# Get your user info
me = client.users.me()

# Print out your information
print("Hello world! " + "My name is " + me['name'] + "!")

client.projects.find_all

b6workspace = client.workspaces.find_by_id(1203279608416517)
decisions_project = client.projects.find_by_id(1203279731709143)
chores_project = client.projects.find_by_id(1203288705129613)
known_projects = [decisions_project, chores_project]
known_project_ids = list(map( lambda x: x["gid"], known_projects))

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


def on_new_tasks(event, callbacks: Iterable[Callable] = []):
    if event["type"] != "task" or \
            event["action"] != "added" or \
            event["parent"]["gid"] not in known_project_ids:
        return
    print("Found a task event!")
    print(event)

    for callback in callbacks:
        callback(event)


def on_new_assignee(event, callbacks: Iterable[Callable] = []):
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
        print(f"New assignee {event['change'].get('new_value', {}).get('name')} added to task: {event['resource']['name']}")

def print_new(event):
    print(event)
    print(f"New task {event['resource']['name']} added to project: {event['parent']['name']}")


def process_events():
    event_generator = get_events_from_resources([chores_project["gid"], decisions_project["gid"]])

    for next_event in event_generator:
        on_new_tasks(next_event, [print_new])
        on_new_assignee(next_event, [print_assignee])


def schedule_test(text):
    print("this text was scheduled for now: " + text)

def main():

    schedule.every(10).seconds.do(process_events)
    schedule.every().saturday.at("15:00").do(schedule_test, text="it's three pm")

    while True:
        schedule.run_pending()
        time.sleep(1)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    while True:
        main()
        # try:
        #     main()
        # except Exception as e:
        #     print("Crashed! restarting...")
        #     print(e)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
