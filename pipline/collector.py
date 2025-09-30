from typing import Any
from asyncio import gather
from helpers.config_helper import get_config
from elasticsearch import AsyncElasticsearch
from helpers.elastic_helper import term_query_sliced
from exceptions.custom_exceptions import DataValidationError, BadDataError

_indexes_names = get_config('data_indexes')


# Fetch a single project by its ID 
async def _fetch_single_project(connection: AsyncElasticsearch, project_id: str) -> dict[str, Any]:
    project_data: dict | None = await term_query_sliced(
        connection,
        _indexes_names["project"],
        "_id",
        project_id
    )
    if not project_data.get(_indexes_names["project"]):
        raise BadDataError(
            message=f"Project with id = ({project_id}) not found!",
            status_code=404
        )
    return list(project_data.values())[0]


# Fetch related tasks and resources to this project
async def _fetch_related_entities(connection: AsyncElasticsearch, project_id: str) -> dict[str, Any]:
    queries = [
        term_query_sliced(connection, index_name=_indexes_names["task"], field="projectid", value=project_id),
        term_query_sliced(connection, index_name=_indexes_names["resource"], field="projectid", value=project_id),
    ]
    results = await gather(*queries)
    return {list(r.keys())[0]: list(r.values())[0] for r in results}


# Ensure that tasks exist for this project 
def _ensure_tasks_exist(data_map: dict[str, Any], project_id: str) -> None:
    if not data_map[_indexes_names["task"]]:
        raise DataValidationError(
            f"No tasks found for project with id =({project_id})!", 500
        )


# fetch project, tasks, and resources, and validate them 
async def gather_project_data(connection: AsyncElasticsearch, project_id: str) -> dict[str, Any]:
    data_map = {}

    data_map[_indexes_names["project"]] = await _fetch_single_project(connection, project_id)

    related_data = await _fetch_related_entities(connection, project_id)

    data_map.update(related_data)

    _ensure_tasks_exist(data_map, project_id)
    
    return data_map
