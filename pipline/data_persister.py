from helpers.io_helpers import get_config, read_json
from elasticsearch import AsyncElasticsearch
from helpers.elastic_helper import compensating_insertion


""" Index reports in Elasticsearch """
async def indexing_reports(connection: AsyncElasticsearch, reports_data: dict[str, list[dict]]) -> None:
    report_indexes = get_config("report_indexes")
    await compensating_insertion(
        es=connection,
        old_index_name=report_indexes["task"],
        mapping=read_json(get_config("paths.mappings.task")),
        data=reports_data["task"],
    )
    await compensating_insertion(
        es=connection,
        old_index_name=report_indexes["resource"],
        mapping=read_json(get_config("paths.mappings.resource")),
        data=reports_data["resource"],
    )
