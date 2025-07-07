from conf.config_and_connection import load_config, connect_elasticsearch
from data.info import generate_project_info
from data.calender import generate_calendars
from data.resource import generate_resources
from data.task import generate_tasks
from jinja2 import Environment, FileSystemLoader

# Reading configurations from config.yaml file
configurations = load_config('conf/config.yaml')


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
    flags = set()
    for item in data_map.get('wbs_tasks', []):
        source = item['_source']
        if source.get('task_linking', ''):
            flags.add(source['task_linking'])

    for item in data_map.get('wbs_resources', []):
        source = item['_source']
        if source.get('resource_group', ''):
            flags.add(source['resource_group'])
        if source.get('resource_type', ''):
            flags.add(source['resource_type'])
    return flags


# Defining several scenarios
def define_scenarios():
    scenarios: list[dict] = []
    # Default scenario = plan
    scenarios.append({'id': 'delayed', 'name': 'Starts with delay'})
    return scenarios


# Defining accounts for all tasks and a main account for project
def define_accounts(datamap):
    accounts = {}
    for item in datamap.get('wbs_tasks', []):
        task_id = item['_id']
        accounts[task_id + "Costs"] =  f"Costs of {task_id}"

    for item in datamap.get('wbs_resources', []):
        source = item['_source']
        account_name = source['cost_center']
        if account_name and account_name not in accounts.keys():
            accounts[account_name] = f"Costs of {account_name}"
    return accounts


# Fetching resource types from resources
def fetch_resource_types(datamap):
    resource_types = set()

    for item in datamap:
        source = item['_source']
        if source.get("resource_type", ''):
            resource_types.add(source["resource_type"])

    return resource_types


# Defining custom properties for tasks
def define_tasks_extends():
    global configurations
    extends: list[dict] = []
    for extend in configurations['extends']['tasks']:
        extends.append({'type': extend['type'], 'id': extend['id'], 'name': extend['name']})
    return extends


# Defining custom properties for resources
def define_resources_extends():
    pass


# Generating TJP file
def generate_tjp(data_map, output_path="TJPs/output.tjp"):
    env = Environment(loader=FileSystemLoader("TJPs"), trim_blocks=True, lstrip_blocks=True)
    template = env.get_template("template.tjp.j2")

    resource_types = fetch_resource_types(data_map.get('wbs_resources', []))

    info = generate_project_info(data_map.get('wbs_info', []))
    calendar = generate_calendars(data_map.get('wbs_calendars', []))
    scenarios = define_scenarios()
    tasks_extends = define_tasks_extends()
    resources_extends_sec = define_resources_extends()
    flags = define_flags(data_map)
    accounts = define_accounts(data_map)
    resources = generate_resources(data_map.get("wbs_resources", []), resource_types)
    tasks = generate_tasks(data_map.get("wbs_tasks", []))

    rendered = template.render(
        info=info,
        calendar=calendar,
        scenarios=scenarios,
        tasks_extends=tasks_extends,
        flags=flags,
        accounts=accounts,
        resources=resources,
        tasks=tasks
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered)


# Running
def main():
    global configurations
    es = connect_elasticsearch(configurations)
    indexes = configurations["indexes"]
    data_map = {}

    print("Fetching data...")
    for index in indexes:
        data_map[index] = fetch_data(es, index)

    print("Generating tjp...")
    generate_tjp(data_map, configurations['tjp_output_path'])
    print(f"[✔️] Generated Successfully: {configurations['tjp_output_path']}")


if __name__ == "__main__":
    main()
