import os
import time
import subprocess
import asyncio
from jinja2 import Environment, FileSystemLoader
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from elasticsearch import AsyncElasticsearch
from helpers.io_helpers import logger
from helpers.elastic_helper import make_connection, write_on_index, term_query, truncate_index
from helpers.config_helper import get_config
from data_models.project import initialize_projects
from data_models.task import initialize_tasks, Task
from data_models.resource import initialize_resources, Resource
from data_models.shift import initialize_shifts
from data_models.scenario import initialize_scenarios
from helpers.utility import cast_string_fields_to_numeric_types
from helpers.io_helpers import read_csv, error_register
from helpers.embedding_helper import embedd_data
from helpers.report_manipulation import manipulation
from exceptions.custom_exceptions import ProcessFailureError, TJ3ProcessError, BadInputError


indexes_names = get_config('data_indexes')

""" Tjp file flags """
def define_flags(tasks: list[Task], resources: list[Resource]):
    flags = set()
    for task in tasks:
        if task.flags:
            flags.update(task.flags)

    for resource in resources:
        if resource.flags:
            flags.update(resource.flags)
            
    return flags


""" Fetching project data from data engine """
async def gather_project_data(connection: AsyncElasticsearch, project_id: str):
    data_map = {}
    project_data: dict | None = await term_query(connection, indexes_names.get('project'), "_id", project_id)
    if not project_data.get(indexes_names["project"]):
        raise BadInputError(message=f"Project with id = ({project_id}) not found!", status_code=404)
    
    data_map[indexes_names['project']] = list(project_data.values())[0]
    queries = []
    queries.append(term_query(connection, indexes_names.get("task"), "projectid", project_id))
    queries.append(term_query(connection, indexes_names.get("resource"), "projectid", project_id))

    results = await asyncio.gather(*queries)
    data_map.update({list(r.keys())[0]: list(r.values())[0] for r in results})
    return data_map

    



""" Tjp file generation """
def generate_tjp(data_map, output_path="tjp_outputs/project.tjp"):
    env = Environment(loader=FileSystemLoader(get_config("paths.templates")),
                      trim_blocks=True, lstrip_blocks=True)
    body_template = env.get_template("main.j2")
    try:
        projects = initialize_projects(data_map.get(indexes_names['project'], [])) 
        shifts = initialize_shifts(data_map.get(indexes_names['shift'], [])) 
        tasks = initialize_tasks(data_map.get(indexes_names['task'], [])) 
        resources = initialize_resources(data_map.get(indexes_names['resource'], [])) 
        scenarios = initialize_scenarios(data_map.get(indexes_names['scenario'], [])) 
        flags = define_flags(tasks, resources)
    except Exception as e:
        message = f"Failed to generate tjp file!\nDetails: {e}"
        raise ProcessFailureError(message, 500)

    report_paths = get_config("paths.reports")
    # Creating reports directory if its not exist
    if not os.path.isdir(report_paths['dir']):
        os.makedirs(report_paths['dir'])

    body = body_template.render(
        project=projects[0],
        scenarios=scenarios,
        shifts=shifts,
        flags=flags,
        resources=resources,
        tasks=tasks,
        reports=report_paths
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(body)


    

""" Indexing reports in elastic search """
async def indexing_reports(connection: AsyncElasticsearch):
    reports_result = dict()
    sources: dict = get_config("paths.reports.files")
    report_dir = get_config("paths.reports.dir")
    
    reports_result = {
        report_name: read_csv(report_dir + "/" + file_name + ".csv")
        for report_name, file_name in sources.items()
        }
    reports_result = {
        report_name: cast_string_fields_to_numeric_types(data) 
        for report_name, data in reports_result.items()
        }
    # Corrections
    manipulation(reports_result)
    report_indexes: dict = get_config("report_indexes")
    # removing previous documents
    await asyncio.gather(*(truncate_index(connection, index) for index in report_indexes.values()))
    for data in reports_result.values():
        for doc in data:
            doc["vector"] = embedd_data(data)
    await asyncio.gather(*(
        write_on_index(connection, data, report_indexes[report_name])
        for report_name, data in reports_result.items()
        if report_name in report_indexes
    ))


""" Processing """
async def main(project_id: str):
    connection = make_connection()

    data_map = await gather_project_data(connection, project_id)
    output_path = get_config("paths.tjp_output")

    generate_tjp(data_map, output_path)
    
    result = subprocess.run(
        "tj3 " + output_path, shell=True, stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE, text=True, encoding='utf-8'
    )
    
    if result.returncode != 0:
        message = f"Failed to finish processing! Because of below errors:\n{result.stderr}"
        await error_register(connection, message)
        raise TJ3ProcessError(message, 500)
    
    await indexing_reports(connection)
    await connection.close()


app = FastAPI()

""" Fast api endpoint """
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



