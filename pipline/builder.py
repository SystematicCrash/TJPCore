import os
import traceback
from jinja2 import Environment, FileSystemLoader
from helpers.config_helper import get_config
from exceptions.custom_exceptions import ProcessFailureError
from models.data_models import Resource, Task
from models.api_models import Scenario
from processors.project_processor import initialize_projects
from processors.resource_processor import initialize_resources
from processors.task_processor import initialize_tasks
from fastapi.exceptions import HTTPException


_data_indexes = get_config('data_indexes')


# Tjp file flags
def _define_flags(tasks: list[Task], resources: list[Resource]) -> set[str]:
    flags = set()
    for task in tasks:
        if task.flags:
            flags.update(task.flags)

    for resource in resources:
        if resource.flags:
            flags.update(resource.flags)
            
    return flags


# Initialize and return jinja template 
def _setup_template_environment() -> Environment:
    return Environment(
        loader=FileSystemLoader(get_config("paths.templates")),
        trim_blocks=True,
        lstrip_blocks=True,
    )


# Initialize projects, tasks, and resources from data map 
def _initialize_entities(data_map: dict, scenario: Scenario) -> tuple:
    try:
        projects = initialize_projects(data_map.get(_data_indexes["project"], []))
        tasks = initialize_tasks(data_map.get(_data_indexes["task"], []), scenario)
        resources = initialize_resources(data_map.get(_data_indexes["resource"], []), scenario)
        flags = _define_flags(tasks, resources)
        return projects, tasks, resources, flags
    except HTTPException as e:
        message = f"Failed to generate tjp file!Details: {e}"
        traceback.print_exc()
        raise ProcessFailureError(message, e.status_code)


# Create reports directory if it doesn't exist 
def _ensure_report_directory() -> dict[str, any]:
    report_paths = get_config("paths.reports")
    if not os.path.isdir(report_paths["dir"]):
        os.makedirs(report_paths["dir"])
    return report_paths


# Render provided entities in the main template file 
def _render_template(env: Environment, projects, tasks, resources, flags, scenario, report_paths: dict) -> str:
    body_template = env.get_template("main.j2")
    return body_template.render(
        project=projects[0],
        scenario=scenario,
        flags=flags,
        resources=resources,
        tasks=tasks,
        reports=report_paths,
    )


# Write the rendered template body to tjp file
def _write_output(body: str, tjp_output: str) -> None:
    with open(tjp_output, "w", encoding="utf-8") as f:
        f.write(body)


# Tjp file generation based on given data
def generate_tjp(data_map: dict, tjp_output="tjp_outputs/project.tjp", scenario: Scenario = None) -> None:
    env = _setup_template_environment()

    projects, tasks, resources, flags = _initialize_entities(data_map, scenario)

    report_paths = _ensure_report_directory()

    body = _render_template(
        env=env, 
        projects=projects, 
        tasks=tasks, 
        resources=resources, 
        flags=flags, 
        scenario=scenario, 
        report_paths=report_paths
        )

    _write_output(body, tjp_output)
