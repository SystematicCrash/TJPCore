from elasticsearch import AsyncElasticsearch, helpers
from helpers.config_helper import get_config
from exceptions.custom_exceptions import ElasticSearchQueryError


# Making connection to DB 
def make_connection():
    conf = get_config("elasticsearch")
    return AsyncElasticsearch(
        conf["host"],
        basic_auth=(conf.get("username"), conf.get("password")) if "username" in conf else None,
        verify_certs=conf.get("verify_certs", True)
    )


# Writing data to an index 
async def write_on_index(connection: AsyncElasticsearch, data, index_name):
    try:
        data = [
            {"_index": index_name, "_id": doc["id"], "_source": doc}
            for doc in data
            ]
        await helpers.async_bulk(connection, data, chunk_size=500, request_timeout=60, refresh=False)
    except Exception as e:
        message = f"\nFailed to write data to index named ({index_name}).\nDetails: {e}"
        raise ElasticSearchQueryError(message, 500)


# Fetching docs from an index 
async def fetch_index(es: AsyncElasticsearch, index_name):
    try:
        query = {
            "_source": {
                "excludes": ["*vector"]
            },
            "query": {
                "match_all": {}
            }
        }
        result = await es.search(index=index_name, body=query, size=10000)
        return {index_name : result['hits']['hits']} or None
    except Exception as e:
        message = f"\nFailed to fetch data from index named ({index_name}).\nDetails: {e}"
        raise ElasticSearchQueryError(message, 500)


# Run custom queries 
async def run_query(es: AsyncElasticsearch, index_name: str, query: dict):
    try:
        result = await es.search(index=index_name, body=query, size=10_000)
        return {index_name : result['hits']['hits']} or None 
    except Exception as e:
        message = f"\nFailed to perform query on index named ({index_name}).\nDetails: {e}"
        raise ElasticSearchQueryError(message, 500)


# Removing all docuements from an index 
async def truncate_index(es: AsyncElasticsearch, index_name: str):
    try:
        await es.delete_by_query(index=index_name, query={"match_all": {}}, conflicts="proceed")
    except Exception as e:
        message = f"\nFailed to truncate index named ({index_name}).\nDetails: {e}"
        raise ElasticSearchQueryError(message, 500)


# Dropping an index
async def drop_index(es: AsyncElasticsearch, index_name: str):
    try:
        await es.indices.delete(index=index_name, ignore=[404])
    except Exception as e:
        message = f"\nFailed to drop index named ({index_name}).\nDetails: {e}"
        raise ElasticSearchQueryError(message, 500)


# Creating a new index 
async def create_index(es: AsyncElasticsearch, index_name: str, mapping_and_setting: dict):
    try:
        await es.indices.create(index=index_name, body=mapping_and_setting)
        await es.cluster.health(wait_for_status="yellow")
    except Exception as e:
        message = f"\nFailed to create index named ({index_name}).\nDetails: {e}"
        raise ElasticSearchQueryError(message, 500)


# Setting alias for index 
async def set_index_alias(es: AsyncElasticsearch, index_name: str, alias: str):
    try:
        body = {
            "actions": [
                {"remove": {"alias": alias, "index": "*"}},
                {"add": {"alias": alias, "index": index_name}}
            ]
        }
        await es.indices.update_aliases(body=body)
    except Exception as e:
        message = f"\nFailed to set alias '{alias}' for index '{index_name}'.\nDetails: {e}"
        raise ElasticSearchQueryError(message, 500)


# Check if a specific index exists or not
async def check_index_exists(es: AsyncElasticsearch, index_name: str):
    try:
        return await es.indices.exists(index=index_name)
    except Exception as e:
        message = f"\nFailed to check existance of index named '{index_name}.\nDetails: {e}'"
        raise ElasticSearchQueryError(message, 500)


# Query by searching a term 
async def term_query(
        es: AsyncElasticsearch, index_name: str, 
        field: str, value: str, sortby=None, order="asc"
        ):
    try:
        query = {
            "_source": {
                "excludes": ["*vector"]
            },
            "query": {
                "match": {
                    field: value
                }
            }
        }
        if sortby:
            query["sort"] = [{sortby: {"order": order}}]
        result = await es.search(index=index_name, body=query, size=10_000)
        return {index_name: result['hits']['hits']} or None
    except Exception as e:
        message = f"\nFailed to perform query on index named ({index_name}).\nDetails: {e}"
        raise ElasticSearchQueryError(message, 500)
    