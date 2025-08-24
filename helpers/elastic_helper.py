from elasticsearch import Elasticsearch, helpers
from concurrent.futures import ThreadPoolExecutor
from helpers.config_helper import get_config
from exceptions.custom_exceptions import ElasticSearchQueryError


# Making connection to DB
def make_connection():
    conf = get_config("elasticsearch")
    return Elasticsearch(
        conf["host"],
        basic_auth=(conf.get("username"), conf.get("password")) if "username" in conf else None,
        verify_certs=conf.get("verify_certs", True)
    )


# Writing data to an index
def write_on_index(connection: Elasticsearch, data, index_name):
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
def fetch_index(es: Elasticsearch, index):
    result = es.search(index=index, body={"_source": {"excludes": ["*vector"]}, "query": {"match_all": {}}}, size=10000)
    return result['hits']['hits']

        

# Run custom queries
def run_query(es: Elasticsearch, index: str, query: dict):
    result = es.search(index=index, body=query, size=10000)
    hits = result['hits']['hits']
    return hits or None