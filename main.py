import traceback
import time
import subprocess
import asyncio
from jinja2 import Environment, FileSystemLoader
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from concurrent.futures import ThreadPoolExecutor
from elasticsearch import AsyncElasticsearch
from helpers.io_helpers import logger
from helpers.elastic_helper import make_connection, write_on_index, run_query, fetch_index
from helpers.config_helper import get_config
from models.project import initialize_projects
from models.task import initialize_tasks, Task
from models.resource import initialize_resources, Resource
from models.account import initialize_accounts
from models.shift import initialize_shifts
from models.scenario import initialize_scenarios
from helpers.utility import cast_string_fields_to_numeric_types
from helpers.io_helpers import read_csv, error_register
from exceptions.custom_exceptions import ProcessFailureError, TJ3ProcessError, BadInputError


indexes_names = get_config('data_indexes')

def define_flags(tasks: list[Task], resources: list[Resource]):
    flags = set()
    for task in tasks:
        if task.flags:
            flags.update(task.flags)

    for resource in resources:
        if resource.flags:
            flags.update(resource.flags)
    return flags



async def gather_project_data(connection: AsyncElasticsearch, project_id: str):
    data_map = {}
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
    project_data: dict | None = await run_query(
        connection, index_name=indexes_names['project'], query=project_query
        )

    if not project_data:
        raise BadInputError(message=f"Project with id = {project_id} not found!", status_code=404)
    
    data_map[indexes_names['project']] = list(project_data.values())[0]
             
    results = await asyncio.gather(
        run_query(connection, index_name=indexes_names['task'], query=tasks_query),
        fetch_index(connection, index_name=indexes_names['resource']),
        fetch_index(connection, index_name=indexes_names['account']),
        fetch_index(connection, index_name=indexes_names['shift']),
        fetch_index(connection, index_name=indexes_names['scenario'])
    )

    data_map.update({list(r.keys())[0]: list(r.values())[0] for r in results})

    return data_map

    



# Generating TJP file
def generate_tjp(data_map, output_path="tjp_outputs/project.tjp"):
    env = Environment(loader=FileSystemLoader(get_config("paths.templates")),
                      trim_blocks=True, lstrip_blocks=True)
    body_template = env.get_template("main.j2")
    try:
        projects = initialize_projects(data_map.get(indexes_names['project'], []))
        shifts = initialize_shifts(data_map.get(indexes_names['shift'], []))
        tasks = initialize_tasks(data_map.get(indexes_names['task'], []))
        resources = initialize_resources(data_map.get(indexes_names['resource'], []))
        accounts = initialize_accounts(data_map.get(indexes_names['account'], []))
        scenarios = initialize_scenarios(data_map.get(indexes_names['scenario'], []))
        flags = define_flags(tasks, resources)
    except Exception as e:
        message = f"Failed to generate tjp file!\nDetails: {e}"
        traceback.print_exc()
        raise ProcessFailureError(message, 500)

    report_path = get_config("paths.reports")
    body = body_template.render(
        project=projects[0],
        scenarios=scenarios,
        shifts=shifts,
        accounts=accounts,
        flags=flags,
        resources=resources,
        tasks=tasks,
        reports=report_path,
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(body)


# Indexing reports into database
def indexing_reports(connection: AsyncElasticsearch):
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
async def main(project_id: str):
    connection = make_connection()
    data_map = await gather_project_data(connection, project_id)

    generate_tjp(data_map, get_config("paths.tjp_output"))
    result = subprocess.run(
        "tj3 " + get_config("paths.tjp_output"), shell=True, stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE, text=True, encoding='utf-8'
    )
    if result.returncode != 0:
        message = f"Failed to finish processing! Because of below errors:\n{result.stderr}"
        error_register(connection, message)
        raise TJ3ProcessError(message, 500)
    connection.close()
    # indexing_reports(connection)


app = FastAPI()


@app.post('/tjp-core/run/{project_id}')
async def run(request: Request, project_id: str):
    auth_header = request.headers.get("authorization")
    expected_token = 'Bearer ' + get_config('api_key')

    if auth_header != expected_token:
        return JSONResponse(content={'status' : 'fail', 'message' : 'Access Denied!'}, status_code=403)
    
    if not project_id:
        return JSONResponse(content={'status' : 'fail', 'message' : 'No project id specified!'}, status_code=400)
    
    start = time.time()
    try:
        await main(project_id)        
    except HTTPException as exp:
        logger(exp.detail,mode='error', console=False)
        return JSONResponse(content={'status' : 'fail', 'message' : exp.detail}, status_code=exp.status_code)
    duration = time.time() - start
    return JSONResponse(
        content={'status' : 'success', 'message' : 'Process finished!', 'duration' : f'{duration:.2f}'},
        status_code=200)




# if __name__ == "__main__":
#     main("proj2025")


