from elasticsearch import Elasticsearch, helpers
from concurrent.futures import ThreadPoolExecutor
from helpers.config_helper import get_config
from exceptions.custom_exceptions import ElasticSearchQueryError


# Making connection to elasticsearch
def make_connection():
    conf = get_config("elasticsearch")
    return Elasticsearch(
        conf["host"],
        basic_auth=(conf.get("username"), conf.get("password")) if "username" in conf else None,
        verify_certs=conf.get("verify_certs", True)
    )


# Writing data to elasticsearch index
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


# Fetching docs from index
def _fetch_index(es: Elasticsearch, index):
    result = es.search(index=index, query={"match_all": {}}, size=10000)
    return result['hits']['hits']


# Fetching from all indexes
def fetch_all_data(es: Elasticsearch, indexes: dict):
    with ThreadPoolExecutor(max_workers=10) as executor:
        try:
            results = {}
            for obj, index_name in indexes.items():
                results[obj] = executor.submit(_fetch_index, es, index_name)
            results = {k: v.result() for k,v in results.items()}
            return results
        except Exception as e:
            message = f"\nError while fetching data from Elasticsearch!\nDetails: {e}"
            raise ElasticSearchQueryError(message, 503)
