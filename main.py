import time
import json
from dataclasses import fields
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from helpers.io_helpers import logger
from helpers.elastic_helper import make_connection, write_on_index, run_query, fetch_index
from helpers.config_helper import get_config
from new_data.project import initialize_projects, Project
from new_data.task import initialize_tasks, Task
from new_data.resource import initialize_resources, Resource
from new_data.account import initialize_accounts, Account
from new_data.shift import initialize_shifts, Shift
from new_data.scenario import initialize_scenarios, Scenario
from jinja2 import Environment, FileSystemLoader
from concurrent.futures import ThreadPoolExecutor
from helpers.utility import colorized_print, cast_string_fields_to_numeric_types
from helpers.io_helpers import read_csv, error_register
from elasticsearch import Elasticsearch
from exceptions.custom_exceptions import ProcessFailureError, \
BadConfigurationError, TJ3ProcessError, ElasticSearchQueryError, BadInputError
import subprocess



def define_flags(tasks, resources):
    flags = set()
    for task in tasks:
        source = task['_source']
        if source.get('flags', []):
            flags.update(source['flags'])

    for resource in resources:
        source = resource['_source']
        if source.get('flags', []):
            flags.update(source['flags'])
    return flags



# Generating TJP file
def generate_tjp(data_map, output_path="tjp_outputs/project.tjp"):
    env = Environment(loader=FileSystemLoader(get_config("paths.templates")),
                      trim_blocks=True, lstrip_blocks=True)
    body_template = env.get_template("main.j2")
    with ThreadPoolExecutor(max_workers=15) as executor:
        try:
            projects = executor.submit(initialize_projects, data_map.get("project", []))
            shifts = executor.submit(initialize_shifts, data_map.get("shifts", []))
            tasks = executor.submit(initialize_tasks, data_map.get("tasks", []))
            resources = executor.submit(initialize_resources, data_map.get("resources", []))
            accounts = executor.submit(initialize_accounts, data_map.get("accounts", []))
            scenarios = executor.submit(initialize_scenarios, data_map.get("scenarios", []))
            flags = executor.submit(define_flags, tasks=data_map.get('tasks', []), resources=data_map.get('resources', []))
        except Exception as e:
            message = f"Failed to generate tjp file!\nDetails: {e}"
            raise ProcessFailureError(message, 500)

    report_path = get_config("paths.reports")
    body = body_template.render(
        project=projects.result()[0],
        scenarios=scenarios.result(),
        shifts=shifts.result(),
        accounts=accounts.result(),
        flags=flags.result(),
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


# Processing
def main(project_id: str):
    project_query = {
        "_source": {
            "excludes": ["*vector"]
        },
        "query": {
            "term": {
                "_id": project_id
            }
        }
    }
    tasks_query = {
        "_source": {
            "excludes": ["*vector"]
        },
        "query": {
            "term": {
                "projectid": project_id
            }
        }
    }
    connection = make_connection()
    data_map = {}
    data_map['project'] = run_query(connection, index=get_config("data_indexes.project"), query=project_query)

    if not data_map['project']:
        raise BadInputError(message=f"Project with id={project_id} not found!", status_code=404)

    data_map['tasks'] = run_query(connection, index=get_config("data_indexes.task"), query=tasks_query)
    data_map['resources'] = fetch_index(connection, index=get_config("data_indexes.resource"))
    data_map['accounts'] = fetch_index(connection, index=get_config("data_indexes.account"))
    data_map['shifts'] = fetch_index(connection, index=get_config("data_indexes.shift"))
    data_map['scenarios'] = fetch_index(connection, index=get_config("data_indexes.scenario"))

    generate_tjp(data_map, get_config("paths.tjp_output"))

    # result = subprocess.run(
    #     "tj3 " + get_config("paths.tjp_output"), shell=True, stdout=subprocess.DEVNULL,
    #     stderr=subprocess.PIPE, text=True, encoding='utf-8'
    # )
    # if result.returncode != 0:
    #     message = f"Failed to finish processing! Because of below errors:\n{result.stderr}"
    #     error_register(connection, message)
    #     raise TJ3ProcessError(message, 500)
    # indexing_reports(connection)

# if __name__ == "__main__":
#     main("proj2025")

app = FastAPI()


@app.post('/tjp-core/run/{project_id}')
async def run(request: Request, project_id: str):
    auth_header = request.headers.get("authorization")
    expected_token = 'Bearer ' + get_config('api_key')

    if auth_header != expected_token:
        return Response('Access Denied!', 403)
    
    if not project_id:
        return Resource('No project id specified!', 400)
    
    start = time.time()
    try:
        main(project_id)
    except HTTPException as exp:
        logger(exp.detail,mode='error', console=False)
        return Response(exp.detail, exp.status_code)
    duration = time.time() - start
    return JSONResponse(
        content={'message' : 'Process finished!', 'duration' : f'{duration:.2f}'},
        status_code=200)


