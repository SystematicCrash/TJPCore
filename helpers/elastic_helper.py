import traceback

from elasticsearch import Elasticsearch, helpers
from helpers.utility import colorized_print
from helpers.io_helpers import logger
from concurrent.futures import ThreadPoolExecutor
from helpers.config_helper import get_config


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
        colorized_print(f"red", f"\nFailed to write data to index named ({index_name}).\nDetails: {e}")
        logger(f"{e}", mode="error", console=False)
        exit(1)


# Fetching docs from index
def fetch_index(es: Elasticsearch, index):
    result = es.search(index=index, query={"match_all": {}}, size=10000)
    return result['hits']['hits']


# Fetching from all indexes
def fetch_all_data(es: Elasticsearch, indexes: dict):
    with ThreadPoolExecutor(max_workers=10) as executor:
        try:
            results = {}
            data_map = {}
            for obj, index_name in indexes.items():
                results[obj] = executor.submit(fetch_index, es, index_name)
            for obj, index_data in results.items():
                data_map[obj] = index_data.result()
            return data_map
        except Exception as e:
            colorized_print("red", f"\nError while fetching data from Elasticsearch!\nDetails:{e}")
            logger(f"{e}", "error", console=False)
            traceback.print_exc()
            exit(1)
