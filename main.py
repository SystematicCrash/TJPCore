from conf.config_and_connection import load_config, connect_elasticsearch
from data.info import generate_project_info
from data.calender import generate_calendars
from data.resource import generate_resources
from data.task import generate_tasks
from jinja2 import Environment, FileSystemLoader
from concurrent.futures import ThreadPoolExecutor
import subprocess
from sys import exit

# Reading configurations from config.yaml file
configurations = load_config('conf/config.yaml')


# Fetching docs from index
def fetch_data(es, index):
    try:
        result = es.search(index=index, query={"match_all": {}}, size=10000)
        return result['hits']['hits']
    except Exception as e:
        print("Cannot make a query on elasticsearch!\nDetails:", e)
        exit(1)


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
    global configurations
    scenarios: list[dict] = []
    # Default scenario = plan
    for scenario in configurations.get('scenarios', []):
        scenarios.append({'id': scenario['id'], 'name': scenario['name']})
    return scenarios


# Defining accounts for all tasks and a main account for project
def define_accounts(datamap):
    accounts = {}
    for item in datamap.get('wbs_tasks', []):
        account = {}
        task_id = item['_id']
        account_id = task_id + "Costs"
        account['name'] = f"Costs of {task_id}"
        account['aggregate'] = 'tasks'
        accounts[account_id] = account

    for item in datamap.get('wbs_resources', []):
        account = {}
        source = item['_source']
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
        trim_blocks=True, lstrip_blocks=True
    )
    body_template = env.get_template("template.tjp.j2")
    report_template = env.get_template("reports.tjp.j2")

    # executor_pool = ThreadPoolExecutor(max_workers=15)
    # with executor_pool as executor:
    #     resource_types = executor.submit(fetch_resource_types, data_map.get('wbs_resources', [])).result()
    #     info = executor.submit(generate_project_info, data_map.get('wbs_info', [])).result()
    #     calendar = executor.submit(generate_calendars, data_map.get('wbs_calendars', [])).result()
    #     scenarios = executor.submit(define_scenarios).result()
    #     tasks_extends = executor.submit(define_tasks_extends).result()
    #     resources_extends = executor.submit(define_resources_extends).result()
    #     flags = executor.submit(define_flags, data_map).result()
    #     accounts = executor.submit(define_accounts, data_map).result()
    #     resources = executor.submit(generate_resources, data_map.get("wbs_resources", []), resource_types).result()
    #     tasks = executor.submit(generate_tasks, data_map.get("wbs_tasks", [])).result()

    resource_types = fetch_resource_types(data_map.get('wbs_resources', []))
    info = generate_project_info(data_map.get('wbs_info', []))
    calendar = generate_calendars(data_map.get('wbs_calendars', []))
    scenarios = define_scenarios()
    tasks_extends = define_tasks_extends()
    resources_extends = define_resources_extends()
    flags = define_flags(data_map)
    accounts = define_accounts(data_map)
    resources = generate_resources(data_map.get("wbs_resources", []), resource_types)
    tasks = generate_tasks(data_map.get("wbs_tasks", []))

    export_path = (configurations.get('paths')).get('exports')

    body = body_template.render(
        info=info,
        calendar=calendar,
        outputdir=export_path,
        scenarios=scenarios,
        tasks_extends=tasks_extends,
        resources_extends=resources_extends,
        flags=flags,
        accounts=accounts,
        resources=resources,
        tasks=tasks
    )
    reports_conf = configurations.get('reports', '')
    reports = ''
    if reports_conf:
        reports = report_template.render(
            text_report=reports_conf['text_report'],
            resource_report=reports_conf['resource_report'],
            task_report=reports_conf['task_report']
        )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(body + reports)


# Running
def main():
    global configurations

    with open('banner.txt', 'r', encoding="utf-8") as f:
        content = f.read()
    print(content)

    es = connect_elasticsearch(configurations)
    indexes = configurations["indexes"]

    print("Fetching data...")
    # TODO test this blocks, with parallel and without it
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {}
        for index in indexes:
            futures[index] = executor.submit(fetch_data, es, index)

    data_map = {}
    for index_name, proceed in futures.items():
        data_map[index_name] = proceed.result()
    # for index in indexes:
    #     data_map[index] = fetch_data(es, index)
    print("Generating tjp...")
    generate_tjp(data_map, configurations['paths']['tjp_output'])
    print(f"[✔️] TJP generated Successfully: {configurations['paths']['tjp_output']}")

    result = subprocess.run("tj3 " + configurations['paths']['tjp_output'], shell=True)
    print("[✔️]Reports generated successfully!") if result.returncode == 0 else print("[]Failed to generate reports!")


if __name__ == "__main__":
    main()
