import os
import traceback
from jinja2 import Environment, FileSystemLoader
from data_models.task import Task, initialize_tasks
from data_models.resource import Resource, initialize_resources
from data_models.project import initialize_projects
from helpers.io_helpers import get_config
from http_api.models import Scenario
from exceptions.custom_exceptions import ProcessFailureError


_indexes_names = get_config('data_indexes')


""" Tjp file flags """
def _define_flags(tasks: list[Task], resources: list[Resource]) -> set[str]:
    flags = set()
    for task in tasks:
        if task.flags:
            flags.update(task.flags)

    for resource in resources:
        if resource.flags:
            flags.update(resource.flags)
            
    return flags


""" Initialize and return jinja template """
def _setup_template_environment() -> Environment:
    return Environment(
        loader=FileSystemLoader(get_config("paths.templates")),
        trim_blocks=True,
        lstrip_blocks=True,
    )


"""Initialize projects, tasks, and resources from data map."""
def _initialize_entities(data_map: dict, scenario: Scenario) -> tuple:
    try:
        projects = initialize_projects(data_map.get(_indexes_names["project"], []))
        tasks = initialize_tasks(data_map.get(_indexes_names["task"], []), scenario)
        resources = initialize_resources(data_map.get(_indexes_names["resource"], []), scenario)
        flags = _define_flags(tasks, resources)
        return projects, tasks, resources, flags
    except Exception as e:
        message = f"Failed to generate tjp file!\nDetails: {e}"
        traceback.print_exc()
        raise ProcessFailureError(message, 500)


""" Create reports directory if it doesn't exist """
def _ensure_report_directory() -> dict[str, any]:
    report_paths = get_config("paths.reports")
    if not os.path.isdir(report_paths["dir"]):
        os.makedirs(report_paths["dir"])
    return report_paths


""" Render provided entities in the main template file """
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


"""Write the rendered template body to tjp file"""
def _write_output(body: str, tjp_output: str) -> None:
    with open(tjp_output, "w", encoding="utf-8") as f:
        f.write(body)


""" Tjp file generation based on given data """
def generate_tjp(data_map: dict, tjp_output="tjp_outputs/project.tjp", scenario: Scenario = None) -> None:
    env = _setup_template_environment()

    projects, tasks, resources, flags = _initialize_entities(data_map, scenario)

    report_paths = _ensure_report_directory()

    body = _render_template(env, projects, tasks, resources, flags, scenario, report_paths)

    _write_output(body, tjp_output)
