from elasticsearch import AsyncElasticsearch, helpers
from concurrent.futures import ThreadPoolExecutor
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
        for item in data:
            actions = [{
                "_index": index_name,
                "_id": item["id"],
                "_source": item
            }]
            helpers.bulk(connection, actions)
    except Exception as e:
        message = f"\nFailed to write data to index named ({index_name}).\nDetails: {e}"
        raise ElasticSearchQueryError(message, 503)


# Fetching docs from an index
async def fetch_index(es: AsyncElasticsearch, index_name):
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

        

# Run custom queries
async def run_query(es: AsyncElasticsearch, index_name: str, query: dict):
    result = await es.search(index=index_name, body=query, size=10000)
    return {index_name : result['hits']['hits']} or None
