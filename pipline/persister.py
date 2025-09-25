from helpers.io_helper import read_json
from helpers.config_helper import get_config
from elasticsearch import AsyncElasticsearch
from helpers.elastic_helper import create_index, \
    check_index_exists, drop_index, write_on_index, set_index_alias
from exceptions.custom_exceptions import ElasticSearchQueryError


# Choosing the correct name for new index
async def _find_new_index_name(es: AsyncElasticsearch, old_index_name: str):
    postfix = 'fresh'
    if await check_index_exists(es, index_name=f"{old_index_name}_{postfix}"):
        postfix = "new"
    if await check_index_exists(es, index_name=f"{old_index_name}_{postfix}"):
        await drop_index(es, index_name=f"{old_index_name}_{postfix}")
    return f"{old_index_name}_{postfix}"



# Reseting indexes and writing data on new indexes (near transactional | compensating action) 
async def _compensating_insertion(es: AsyncElasticsearch, old_index_name: str, mapping: dict, data: dict):

    new_index_name = await _find_new_index_name(es, old_index_name)
    try:
        await create_index(es, new_index_name, mapping)
        await write_on_index(es, data, new_index_name)

        if new_index_name.endswith("fresh"):
            await drop_index(es, f"{old_index_name}_new")
        else:
            await drop_index(es, f"{old_index_name}_fresh")
        await set_index_alias(es, index_name=new_index_name, alias=old_index_name)

    except Exception as e:
        if await check_index_exists(es, new_index_name):
            await drop_index(es, new_index_name)
        message = f"\nCompensating insertion failed for index '{old_index_name}'.\nDetails: {e}"
        raise ElasticSearchQueryError(message, 500)


# Index reports in Elasticsearch
async def indexing_reports(connection: AsyncElasticsearch, reports_data: dict[str, list[dict]]) -> None:
    report_indexes = get_config("report_indexes")

    for key in report_indexes.keys():
        await _compensating_insertion(
            es=connection,
            old_index_name=report_indexes[key],
            mapping=read_json(get_config(f"paths.mappings.{key}")),
            data=reports_data[key],
        )
