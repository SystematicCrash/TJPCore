from elasticsearch import Elasticsearch
import ijson


# Load config only once when the module is first imported
def _load_config(path="conf/config.json"):
    with open(path, 'r') as f:
        return next(ijson.items(f, '', multiple_values=False))


# Global variable that holds the config
_config = _load_config()


# Reading a specific property from config
def get_config(property_name=None):
    if property_name is None:
        raise Exception("property_name cannot be None")
    keys = property_name.split(".")
    value = _config
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            raise KeyError(f"Invalid property name: {property_name}")
    return value


# Making connection to elasticsearch
def connect_elasticsearch():
    conf = get_config("elasticsearch")
    return Elasticsearch(
        conf["host"],
        basic_auth=(conf.get("username"), conf.get("password")) if "username" in conf else None,
        verify_certs=conf.get("verify_certs", True)
    )
