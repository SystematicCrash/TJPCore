from conf.config_and_connection import connect_elasticsearch, get_config
from data.info import generate_project_info
from data.calender import generate_calendars
from data.resource import generate_resources
from data.task import generate_tasks, Task
from jinja2 import Environment, FileSystemLoader
from concurrent.futures import ThreadPoolExecutor
from src.utility import colorized_print, convert_csv_to_json, logger, read_json
from elasticsearch import Elasticsearch, helpers
import time
import subprocess
from sys import exit
from os import path


# Writing data to elasticsearch index
def write_on_index(connection: Elasticsearch, data, index_name):
    try:
        for item in data:
            actions = [{
                "_index": index_name,
                "_id": item["id"],
                "_source": item
            }]
            helpers.bulk(connection, actions)
    except Exception as e:
        colorized_print(f"red", f"Failed to write data to index named ({index_name}).\nDetails: {e}")
        exit(1)


# Fetching docs from index
def fetch_index(es: Elasticsearch, index):
    result = es.search(index=index, query={"match_all": {}}, size=10000)
    return result['hits']['hits']


# Fetching from all indexes
def fetch_all_data(es: Elasticsearch, indexes):
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
            colorized_print("red", f"Error while fetching data from Elasticsearch!\nDetails:{e}")
            logger(f"{e}", "error", console=False)
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
    scenarios: list[dict] = []
    # Default scenario = plan
    for scenario in get_config("scenarios"):
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
    extends: list[dict] = []
    for extend in get_config("extends.tasks"):
        extends.append({'type': extend['type'], 'id': extend['id'], 'name': extend['name']})
    return extends


# Defining custom properties for resources
def define_resources_extends():
    extends: list[dict] = []
    for extend in get_config("extends.resources"):
        extends.append({'type': extend['type'], 'id': extend['id'], 'name': extend['name']})
    return extends


# Reports definition
def define_reports():
    reports: list[dict] = []
    for report in get_config("reports"):
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
    env = Environment(loader=FileSystemLoader(get_config("paths.templates")),
                      trim_blocks=True, lstrip_blocks=True)
    body_template = env.get_template("main.j2")
    with ThreadPoolExecutor(max_workers=15) as executor:
        try:
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
        except Exception as e:
            colorized_print("red", f"{e}")
            logger(f"{e}", "error", console=False)

    export_path = get_config("paths.exports")
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


# Saving report result into the database indexes
def indexing_reports(connection: Elasticsearch):
    csv_dir = get_config("paths.exports.dirs.csv_dir")
    json_dir = get_config("paths.exports.dirs.json_dir")
    for file_name in get_config("paths.exports.files"):
        csv_path = csv_dir + file_name + '.csv'
        json_path = json_dir + file_name + '.json'
        if not path.exists(csv_path):
            colorized_print('red', f"Path does not exist: {csv_path} in config.json: paths->exports->csv_path")
            exit(1)
        convert_csv_to_json(csv_path, json_path)
        json_data = read_json(json_path)
        # write_on_index(connection, json_data, index_name=file_name)


# Running
def main():
    start = time.time()
    with open('banner.txt', 'r', encoding="utf-8") as f:
        content = f.read()
        colorized_print('blue', content)
    colorized_print("light-cyan", "processing...")
    connection = connect_elasticsearch()
    indexes = get_config('data_indexes')
    data_map = fetch_all_data(connection, indexes)
    generate_tjp(data_map, get_config("paths.tjp_output"))
    result = subprocess.run("tj3 " + get_config("paths.tjp_output"),
                            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, encoding='utf-8')
    if result.returncode != 0:
        colorized_print('red', f"Failed to finish processing! Because of below errors:\n{result.stderr}")
        logger(f"{result.stderr}", "error", console=False)
        exit(1)
    indexing_reports(connection)
    duration = time.time() - start
    colorized_print("light-green", "Done!")
    colorized_print('light-yellow', f"Duration: {duration:.2f}s")


if __name__ == "__main__":
    main()
