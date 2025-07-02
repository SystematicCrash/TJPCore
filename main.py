from conf.config_and_connection import load_config, connect_elasticsearch
from data.info import generate_project_info
from data.calender import generate_calendars
from data.resource import generate_resources
from data.task import generate_tasks


# Fetching docs from index
def fetch_data(es, index):
    try:
        result = es.search(index=index, query={"match_all": {}}, size=10000)
        return result['hits']['hits']
    except Exception as e:
        print("Cannot make a query on elasticsearch!\nDetails:", e)
        quit(1)


# Defining flags from task_linking and resource_group fields (just from tasks index)
def define_flags(data_map):
    content = ''
    flags = set()
    for item in data_map.get('wbs_tasks', []):
        body = item['_source']
        if body.get('task_linking', ''):
            flags.add(body["task_linking"])

    for item in data_map.get('wbs_resources', []):
        body = item['_source']
        if body.get('resource_group', ''):
            flags.add(body["resource_group"])

    if flags:
        content += "flags\n"
        content += ",\n".join(flags)
    return content


# Defining several scenarios
def define_scenarios():
    content = ''
    scenarios_lines = []
    scenarios_lines.append(f"scenario plan \"Plan\" {{")
    scenarios_lines.append(f"  scenario delayedStart \"Starts with delay\"")
    scenarios_lines.append("}")
    content += "\n".join(scenarios_lines)
    return content


# Defining accounts for all tasks and a main account for project
def define_accounts(datamap):
    content = ''
    account_lines = [f"account ProjectCosts \"Costs of the project\" {{"]
    for item in datamap.get('wbs_tasks', []):
        task_id = item['_id']
        account_lines.append(f"  account {task_id + "Costs"} \"Costs of {task_id}\"")

    for item in datamap.get('wbs_resources', []):
        account_name = item['cost_center']
        if account_name:
            account_lines.append(f"  account \"{account_name}\" \"Costs of {account_name}\"")

    account_lines.append("}")
    content += '\n'.join(account_lines)
    return content


# Fetching resource types from resources
def fetch_resource_types(datamap):
    resource_types = set()

    for item in datamap:
        body = item['_source']
        if body.get("resource_type", ''):
            resource_types.add(body["resource_type"])

    return resource_types


# Generating TJP file
def generate_tjp(data_map, output_path="outputs/outputs.tjp"):
    resource_types = fetch_resource_types(data_map.get('wbs_resources', []))
    project_sec = generate_project_info(data_map.get('wbs_info', []))
    calendar_info = generate_calendars(data_map.get('wbs_calendars', []))
    scenarios_sec = define_scenarios()
    flags_sec = define_flags(data_map)
    accounts_sec = define_accounts(data_map)
    resource_sec = generate_resources(data_map.get("wbs_resources", []), resource_types)
    task_sec = generate_tasks(data_map.get("wbs_tasks", []))

    content = (
            project_sec
            + calendar_info
            + scenarios_sec
            + "\n"
            + flags_sec
            + "\n"
            + accounts_sec
            + "\n\n"
            + resource_sec
            + "\n\n"
            + task_sec
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


# Running
def main():
    config = load_config()
    es = connect_elasticsearch(config)
    indexes = config["data"]
    data_map = {}

    print("Fetching data...")
    for index in indexes:
        data_map[index] = fetch_data(es, index)

    print("Generating tjp...")
    generate_tjp(data_map, config['tjp_output_path'])
    print(f"[✔️] Generated Successfully: {config['tjp_output_path']}")


if __name__ == "__main__":
    main()
