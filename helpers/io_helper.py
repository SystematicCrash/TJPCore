import csv
import json
import logging
from os import path
from helpers.config_helper import get_config
from helpers.utility import colorized_print
from elasticsearch import Elasticsearch
from uuid import uuid4
import logging
from pathlib import Path



def generating_json_file_from_csv(csv_path: str, json_path: str):
    if not path.exists(csv_path):
        message = f"Path does not exist: {csv_path} in config.json: paths->reports->csv_path"
        colorized_print('red', message)
        exit(1)
    with open(csv_path, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        content = list(reader)
    with open(json_path, mode='w', newline='', encoding='utf-8') as jsonfile:
        json.dump(content, jsonfile, ensure_ascii=False, indent=4)


def read_csv(csv_path: str):
    with open(csv_path, mode='r', newline='', encoding='utf-8') as csvfile:
        return list(csv.DictReader(csvfile, delimiter=';'))


def read_json(json_path: str):
    with open(json_path, mode='r', newline='', encoding='utf-8') as jsonfile:
        return json.load(jsonfile)


# Writing logical tj3 errors on elasticsearch index 
async def error_register(connection: Elasticsearch, error_message: str):
    from helpers.elastic_helper import write_on_index, drop_index, create_index
    index_name = get_config("error_index")
    if not get_config("exceptions.save_logs_in_db"):
        return
    data = {'id': uuid4().hex, 'message': error_message}
    await drop_index(connection, index_name)
    await create_index(connection, index_name, read_json("mappings/error_index_mapping.json"))
    await write_on_index(connection, [data], get_config('error_index'))
