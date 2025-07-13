from conf.config_and_connection import load_config, connect_elasticsearch
from data.info import generate_project_info
from data.calender import generate_calendars
from data.resource import generate_resources
from data.task import generate_tasks, Task
from jinja2 import Environment, FileSystemLoader
from concurrent.futures import ThreadPoolExecutor
from data.utility import colorized_print
import subprocess
from sys import exit

# Reading configurations from config.yaml file
configurations = load_config('conf/config.yaml')


# Fetching docs from index
def fetch_index(es, index):
    result = es.search(index=index, query={"match_all": {}}, size=10000)
    return result['hits']['hits']


# Fetching from all indexes
def fetch_all_data(es, indexes):
    with ThreadPoolExecutor(max_workers=10) as executor:
        try:
            results = {}
            data_map = {}
            for index in indexes:
                results[index] = executor.submit(fetch_index, es, index)
            for index_name, index_data in results.items():
                data_map[index_name] = index_data.result()
            return data_map
        except Exception as e:
            colorized_print('yellow', "❌Error fetching data from elasticsearch")
            colorized_print('red', f"Details: {e}")
            exit(1)


# Flags definition from task_linking and resource_group fields (just from tasks index)
def define_flags(tasks, resources):
    flags = set()
    for task in tasks:
        source = task['_source']
        if source.get('task_linking', ''):
            flags.add(source['task_linking'])

    for resource in resources:
        source = resource['_source']
        if source.get('resource_group', ''):
            flags.add(source['resource_group'])
        if source.get('resource_type', ''):
            flags.add(source['resource_type'])
    return flags


# Defining several scenarios
def define_scenarios():
    global configurations
    scenarios: list[dict] = []
    # Default scenario = plan
    for scenario in configurations.get('scenarios', []):
        scenarios.append({'id': scenario['id'], 'name': scenario['name']})
    return scenarios


# Tasks accounts definition
def define_tasks_accounts(tasks: list[Task]):
    accounts = {}
    for task in tasks:
        account = {}
        account_id = task.task_id + "Costs"
        account['name'] = f"Costs of {task.task_id}"
        account['aggregate'] = 'tasks'
        accounts[account_id] = account
    return accounts


# Resources accounts definition
def define_resources_accounts(resources):
    accounts = {}
    for resource in resources:
        account = {}
        source = resource['_source']
        account_id = source['cost_center']
        if not account_id in accounts.keys():
            account['name'] = f"Costs of {account_id}"
            account['aggregate'] = 'resources'
            accounts[account_id] = account
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
    global configurations
    extends: list[dict] = []
    for extend in configurations['extends']['resources']:
        extends.append({'type': extend['type'], 'id': extend['id'], 'name': extend['name']})
    return extends


# Generating TJP file
def generate_tjp(data_map, output_path="tjp_outputs/project.tjp"):
    global configurations
    env = Environment(
        loader=FileSystemLoader(configurations['paths']['templates']),
        trim_blocks=True, lstrip_blocks=True)
    body_template = env.get_template("main.j2")
    with ThreadPoolExecutor(max_workers=15) as executor:
        info = executor.submit(generate_project_info, data_map.get('wbs_info', [])).result()
        calendar = executor.submit(generate_calendars, data_map.get('wbs_calendars', [])).result()
        scenarios = executor.submit(define_scenarios).result()
        resource_types = executor.submit(fetch_resource_types, data_map.get('wbs_resources', [])).result()
        resources = executor.submit(generate_resources, data_map.get("wbs_resources", []), resource_types).result()
        tasks = executor.submit(generate_tasks, data_map.get("wbs_tasks", [])).result()
        tasks_extends = executor.submit(define_tasks_extends).result()
        resources_extends = executor.submit(define_resources_extends).result()
        flags = executor.submit(define_flags, tasks=data_map.get('wbs_tasks', []),
                                resources=data_map.get('wbs_resources', [])).result()
        tasks_accounts = executor.submit(define_tasks_accounts, tasks).result()
        resources_accounts = executor.submit(define_resources_accounts, data_map.get("wbs_resources", [])).result()

    # info = generate_project_info(data_map.get('wbs_info', []))
    # calendar = generate_calendars(data_map.get('wbs_calendars', []))
    # scenarios = define_scenarios()
    # resource_types = fetch_resource_types(data_map.get('wbs_resources', []))
    # resources = generate_resources(data_map.get("wbs_resources", []), resource_types)
    # tasks = generate_tasks(data_map.get("wbs_tasks", []))
    # tasks_extends = define_tasks_extends()
    # resources_extends = define_resources_extends()
    # flags = define_flags(tasks=data_map.get('wbs_tasks', []), resources=data_map.get('wbs_resources', []))
    # tasks_accounts = define_tasks_accounts(tasks)
    # resources_accounts = define_resources_accounts(data_map.get("wbs_resources", []))
    export_path = configurations['paths']['exports']
    reports_conf = configurations['reports']

    body = body_template.render(
        info=info,
        calendar=calendar,
        outputdir=export_path,
        scenarios=scenarios,
        tasks_extends=tasks_extends,
        resources_extends=resources_extends,
        flags=flags,
        accounts=tasks_accounts | resources_accounts,
        resources=resources,
        tasks=tasks,
        text_report=reports_conf['text_report'],
        resource_report=reports_conf['resource_report'],
        task_report=reports_conf['task_report']
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(body)


# Running
def main():
    global configurations

    with open('banner.txt', 'r', encoding="utf-8") as f:
        content = f.read()
    colorized_print('light-blue', content)

    es = connect_elasticsearch(configurations)
    indexes = configurations["indexes"]

    colorized_print('cyan', "🔸 Fetching data...")
    data_map = fetch_all_data(es, indexes)
    colorized_print('green', "✔️ Finished.")

    colorized_print('cyan', "🔸 Generating tjp...")
    generate_tjp(data_map, configurations['paths']['tjp_output'])
    colorized_print('green', f"✔️ Finished.")
    print("output: " + configurations['paths']['tjp_output'])

    colorized_print('cyan', "🔸 Running TJ3...")
    result = subprocess.run("tj3 " + configurations['paths']['tjp_output'],
                            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, encoding='utf-8')
    if result.returncode == 0:
        colorized_print('green', "✔️ Reports generated successfully!")
        print("export: " + configurations['paths']['exports'])
    else:
        colorized_print('yellow', "❌ Failed to finish processing! Because of below errors:")
        colorized_print('red', result.stderr)


if __name__ == "__main__":
    main()
