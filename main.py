import os
import subprocess
import asyncio
from http_api.models import Scenario
from jinja2 import Environment, FileSystemLoader
from elasticsearch import AsyncElasticsearch
from helpers.elastic_helper import make_connection, term_query, compensating_insertion
from helpers.config_helper import get_config
from data_models.project import initialize_projects
from data_models.task import initialize_tasks, Task
from data_models.resource import initialize_resources, Resource
from helpers.io_helpers import read_csv, read_json, error_register
from helpers.report_manipulation import manipulation
from exceptions.custom_exceptions import ProcessFailureError, TJ3ProcessError, BadInputError, DataValidationError


_indexes_names = get_config('data_indexes')



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
    project_data: dict | None = await term_query(connection, _indexes_names.get('project'), "_id", project_id)
    if not project_data.get(_indexes_names["project"]):
        raise BadInputError(message=f"Project with id = ({project_id}) not found!", status_code=404)
    
    data_map[_indexes_names['project']] = list(project_data.values())[0]
    queries = []
    queries.append(term_query(connection, _indexes_names.get("task"), "projectid", project_id))
    queries.append(term_query(connection, _indexes_names.get("resource"), "projectid", project_id))

    results = await asyncio.gather(*queries)
    data_map.update({list(r.keys())[0]: list(r.values())[0] for r in results})

    if not data_map[_indexes_names['resource']]:
        raise DataValidationError(f"No resources found for project with id =({project_id})!", 500)

    if not data_map[_indexes_names['task']]:
        raise DataValidationError(f"No tasks found for project with id =({project_id})!", 500)
    return data_map

    



""" Tjp file generation """
def generate_tjp(data_map, output_path="tjp_outputs/project.tjp", scenario:Scenario = None):
    env = Environment(loader=FileSystemLoader(get_config("paths.templates")),
                      trim_blocks=True, lstrip_blocks=True)
    body_template = env.get_template("main.j2")
    try:
        projects = initialize_projects(data_map.get(_indexes_names['project'], [])) 
        tasks = initialize_tasks(data_map.get(_indexes_names['task'], []), scenario) 
        resources = initialize_resources(data_map.get(_indexes_names['resource'], []), scenario) 
        flags = define_flags(tasks, resources)
    except Exception as e:
        message = f"Failed to generate tjp file!\nDetails: {e}"
        import traceback
        traceback.print_exc()
        raise ProcessFailureError(message, 500)

    report_paths = get_config("paths.reports")
    # Creating reports directory if its not exist
    if not os.path.isdir(report_paths['dir']):
        os.makedirs(report_paths['dir'])
    # Putting data in template file
    body = body_template.render(
        project=projects[0],
        scenario=scenario,
        flags=flags,
        resources=resources,
        tasks=tasks,
        reports=report_paths
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(body)



""" Get reports result as a dictionary """
def get_reports_result():
    reports_result = dict()
    sources: dict = get_config("paths.reports.files")
    report_dir = get_config("paths.reports.dir")
    reports_result = {
        report_name: read_csv(report_dir + "/" + file_name + ".csv")
        for report_name, file_name in sources.items()
    }
    # Corrections
    manipulation(reports_result)
    return reports_result



""" Indexing reports in elastic search """
async def indexing_reports(connection: AsyncElasticsearch, reports_result: dict):
    report_indexes = get_config('report_indexes')

    await compensating_insertion(
        es=connection, 
        old_index_name=report_indexes.get("task"),
        mapping=read_json(get_config("paths.mappings.task")),
        data=reports_result.get("task")
    )
    await compensating_insertion(
        es=connection, 
        old_index_name=report_indexes.get("resource"),
        mapping=read_json(get_config("paths.mappings.resource")),
        data=reports_result.get("resource")
    )




""" Processing """
async def main(project_id: str, scenario: Scenario = None):
    connection = make_connection()
    data_map = await gather_project_data(connection, project_id)
    output_path = get_config("paths.tjp_output")

    generate_tjp(data_map, output_path, scenario)
    
    result = subprocess.run(
        "tj3 " + output_path, shell=True, stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE, text=True, encoding='utf-8'
    )
    if result.returncode != 0:
        message = f"Failed to finish processing! Because of below errors:\n{result.stderr}"
        await error_register(connection, message)
        raise TJ3ProcessError(message, 500)
    reports_result = get_reports_result()
    """ No need to indexing data in scenario mode """
    if not scenario:
        await indexing_reports(connection, reports_result)
    else:
        return reports_result
    await connection.close()




