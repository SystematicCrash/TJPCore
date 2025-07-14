from conf.config_and_connection import load_config, connect_elasticsearch
from data.info import generate_project_info
from data.calender import generate_calendars
from data.resource import generate_resources
from data.task import generate_tasks, Task
from jinja2 import Environment, FileSystemLoader
from concurrent.futures import ThreadPoolExecutor
from src.utility import colorized_print, read_csv, convert_csv_to_json
import time
import subprocess
from sys import exit
from os import path

# Reading configurations from config.yaml file
configurations = load_config('conf/config.json')


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
    for extend in configurations.get('extends', {}).get('tasks', {}):
        extends.append({'type': extend['type'], 'id': extend['id'], 'name': extend['name']})
    return extends


# Defining custom properties for resources
def define_resources_extends():
    global configurations
    extends: list[dict] = []
    for extend in configurations.get('extends', {}).get('resources', {}):
        extends.append({'type': extend['type'], 'id': extend['id'], 'name': extend['name']})
    return extends


# Reports definition
def define_reports():
    global configurations

    reports: list[dict] = []
    for report in configurations.get('reports', []):
        if report['type'] not in ['task', 'resource', 'account', 'trace']:
            raise ValueError(
                "Invalid report type declared! report type must be 'task', 'resource', 'account' or 'trace'")
        reports.append({
            'type': report['type'] + 'report',
            'id': report['id'], 'name': report['name'],
            'formats': report['formats'], 'columns': report['columns']
        })
    return reports


# Generating TJP file
def generate_tjp(data_map, output_path="tjp_outputs/project.tjp"):
    global configurations

    env = Environment(loader=FileSystemLoader(configurations['paths']['templates']),
                      trim_blocks=True, lstrip_blocks=True)
    body_template = env.get_template("main.j2")

    with ThreadPoolExecutor(max_workers=15) as executor:
        info = executor.submit(generate_project_info, data_map.get('wbs_info', []))
        calendar = executor.submit(generate_calendars, data_map.get('wbs_calendars', []))
        scenarios = executor.submit(define_scenarios)
        resource_types = executor.submit(fetch_resource_types, data_map.get('wbs_resources', []))
        resources = executor.submit(generate_resources, data_map.get("wbs_resources", []), resource_types.result())
        tasks = executor.submit(generate_tasks, data_map.get("wbs_tasks", []))
        tasks_extends = executor.submit(define_tasks_extends)
        resources_extends = executor.submit(define_resources_extends)
        flags = executor.submit(define_flags, tasks=data_map.get('wbs_tasks', []),
                                resources=data_map.get('wbs_resources', []))
        tasks_accounts = executor.submit(define_tasks_accounts, tasks.result())
        resources_accounts = executor.submit(define_resources_accounts, data_map.get("wbs_resources", []))

    export_path = configurations['paths']['exports']

    body = body_template.render(
        info=info.result(),
        calendar=calendar.result(),
        scenarios=scenarios.result(),
        tasks_extends=tasks_extends.result(),
        resources_extends=resources_extends.result(),
        flags=flags.result(),
        accounts=tasks_accounts.result() | resources_accounts.result(),
        resources=resources.result(),
        tasks=tasks.result(),
        exports=export_path,
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(body)



def indexing_reports():
    global configurations

    base_dir = configurations['paths']['exports']['base_dir']

    for file in configurations['paths']['exports']:
        file_path = base_dir + file + '.csv'
        if path.exists(file_path):
            convert_csv_to_json(file_path, file_path.replace('.csv', '.json'))

# Running
def main():
    global configurations

    start = time.time()

    with open('banner.txt', 'r', encoding="utf-8") as f:
        content = f.read()
        colorized_print('blue', content)

    connection = connect_elasticsearch(configurations)
    indexes = configurations.get("data_indexes", [])

    colorized_print('cyan', "🔸 Fetching data...")
    data_map = fetch_all_data(connection, indexes)
    colorized_print('green', "✔️ Finished")

    colorized_print('cyan', "🔸 Generating tjp...")
    generate_tjp(data_map, configurations['paths']['tjp_output'])
    colorized_print('green', f"✔️ Finished")

    colorized_print('cyan', "🔸 Running TJ3...")
    result = subprocess.run("tj3 " + configurations['paths']['tjp_output'],
                            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, encoding='utf-8')
    if result.returncode == 0:
        colorized_print('green', f"✔️ Finished")
    else:
        colorized_print('yellow', "❌ Failed to finish processing! Because of below errors:")
        colorized_print('red', result.stderr)

    colorized_print('cyan', "🔸 Indexing reports...")
    indexing_reports()
    colorized_print('green', f"✔️ Finished")

    colorized_print('light-cyan', "All Done!")
    duration = time.time() - start

    colorized_print('light-yellow', f"Duration: {duration:.2f}s")

if __name__ == "__main__":
    main()
