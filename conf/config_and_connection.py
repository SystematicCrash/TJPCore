import yaml
from elasticsearch import Elasticsearch


# Reading conf.yaml
def load_config(path="conf/conf.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# Making connection to elasticsearch
def connect_elasticsearch(config):
    es_conf = config["elasticsearch"]
    return Elasticsearch(
        es_conf["hosts"],
        basic_auth=(es_conf.get("username"), es_conf.get("password")) if "username" in es_conf else None,
        verify_certs=es_conf.get("verify_certs", True)
    )
