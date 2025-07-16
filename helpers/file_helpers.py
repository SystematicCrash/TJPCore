import csv
import json
import logging
from os import path
from helpers.config_helper import get_config
from helpers.utility import colorized_print


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


def logger(message: str, mode: str = 'warning', console: bool = True):
    if mode not in ['debug', 'info', 'warning', 'error', 'critical']:
        raise ValueError(f"{mode} is not a valid mode")
    if console:
        logging.basicConfig(level=mode.upper(), format="{levelname}: {message}", style='{')
    else:
        logging.basicConfig(
            filename=get_config('logging.filename'),
            filemode=get_config('logging.filemode'),
            level=mode.upper(), format="{levelname}: {message} - {asctime}",
            datefmt="%Y-%m-%d %H:%M:%S", style='{')
    if mode == 'debug':
        logging.debug(message)
    elif mode == 'info':
        logging.info(message)
    elif mode == 'warning':
        logging.warning(message)
    elif mode == 'error':
        logging.error(message)
    elif mode == 'critical':
        logging.critical(message)
