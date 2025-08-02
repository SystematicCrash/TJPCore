import traceback

from helpers.elastic_helper import make_connection, fetch_all_data, write_on_index
from helpers.config_helper import get_config
from data.info import generate_project_info
from data.calender import generate_calendars
from data.resource import generate_resources
from data.task import generate_tasks, Task
from jinja2 import Environment, FileSystemLoader
from concurrent.futures import ThreadPoolExecutor
from helpers.utility import colorized_tqdm_write, cast_string_fields_to_numeric_types, progress_bar
from helpers.io_helpers import logger, read_csv, error_register
from elasticsearch import Elasticsearch
import time
import subprocess
import threading
from helpers import utility
from sys import exit


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
        source = resource.get('_source', {})
        account_id = source.get('cost_center', '')
        if account_id and not account_id in accounts.keys():
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
            info = executor.submit(generate_project_info, data_map.get('info', []))
            calendar = executor.submit(generate_calendars, data_map.get('calendar', []))
            scenarios = executor.submit(define_scenarios)
            resource_types = executor.submit(fetch_resource_types, data_map.get('resource', []))
            resources = executor.submit(generate_resources, data_map.get("resource", []), resource_types.result())
            tasks = executor.submit(generate_tasks, data_map.get("task", []))
            tasks_extends = executor.submit(define_tasks_extends)
            resources_extends = executor.submit(define_resources_extends)
            flags = executor.submit(define_flags, tasks=data_map.get('task', []),
                                    resources=data_map.get('resource', []))
            tasks_accounts = executor.submit(define_tasks_accounts, tasks.result())
            resources_accounts = executor.submit(define_resources_accounts, data_map.get("resource", []))
        except Exception as e:
            message = f"Failed to generate tjp file!\nDetails: {e}"
            colorized_tqdm_write("red", message)
            logger(message, "error", console=False)
            exit(1)

    report_path = get_config("paths.reports")
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
        reports=report_path,
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(body)


# Indexing reports into database
def indexing_reports(connection: Elasticsearch):
    reports_result = dict()
    sources: dict = get_config("paths.reports.files")
    csv_dir = get_config("paths.reports.dirs.csv_dir")
    for report_name, file_name in sources.items():
        reports_result[report_name] = read_csv(csv_dir + file_name + ".csv")
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {}
        for k, v in reports_result.items():
            futures[k] = executor.submit(cast_string_fields_to_numeric_types, v)
        reports_result = {k: v.result() for k,v in futures.items()}
        for report_name, data in reports_result.items():
            for component, index_name in dict(get_config("report_indexes")).items():
                if report_name.__contains__(component):
                    executor.submit(write_on_index, connection, data, index_name)


# Running
def main():
    with open('banner.txt', 'r', encoding="utf-8") as f:
        content = f.read()
        colorized_tqdm_write('blue', content)
    animation_thread = threading.Thread(target=progress_bar)
    animation_thread.daemon = True
    animation_thread.start()
    connection = make_connection()
    utility.progress += 200
    data_map = fetch_all_data(connection, get_config("data_indexes"))
    utility.progress += 200
    generate_tjp(data_map, get_config("paths.tjp_output"))
    utility.progress += 200
    result = subprocess.run("tj3 " + get_config("paths.tjp_output"),
                            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, encoding='utf-8')
    utility.progress += 200
    if result.returncode != 0:
        message = f"Failed to finish processing! Because of below errors:\n{result.stderr}"
        colorized_tqdm_write('red', message)
        error_register(connection, message)
        logger(message, "error", console=False)
        exit(1)
    utility.progress += 200
    indexing_reports(connection)
    utility.progress += 200
    utility.end_of_process = True


if __name__ == "__main__":
    start = time.time()
    main()
    duration = time.time() - start
    print('Done!')
    print(f'Duration: {duration}s')
    colorized_tqdm_write("light-green", "...Done!")
    colorized_tqdm_write('light-yellow', f"Duration: {duration:.2f}s")

