import yaml
from elasticsearch import Elasticsearch


# Reading conf.yaml
def load_config(path="conf/config.json"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# Making connection to elasticsearch
def connect_elasticsearch(config):
    conf = config["elasticsearch"]
    return Elasticsearch(
        conf["host"],
        basic_auth=(conf.get("username"), conf.get("password")) if "username" in conf else None,
        verify_certs=conf.get("verify_certs", True)
    )
