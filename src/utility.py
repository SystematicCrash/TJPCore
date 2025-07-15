from colorama import Fore, Style as st
import csv, json
import logging
from conf.config_and_connection import get_config



def day_to_an_abbreviation(days: str):
    days = days.replace("Saturday", "sat")
    days = days.replace("Sunday", "sun")
    days = days.replace("Monday", "mon")
    days = days.replace("Tuesday", "tue")
    days = days.replace("Wednesday", "wed")
    days = days.replace("Thursday", "thu")
    days = days.replace("Friday", "fri")
    return days


def colorized_print(color: str, text: str):
    colors = {
        'blue': Fore.BLUE,
        'red': Fore.RED,
        'cyan': Fore.CYAN,
        'yellow': Fore.YELLOW,
        'white': Fore.WHITE,
        'green': Fore.GREEN,
        'light-blue': Fore.LIGHTBLUE_EX,
        'light-green': Fore.LIGHTGREEN_EX,
        'light-red': Fore.LIGHTRED_EX,
        'light-white': Fore.LIGHTWHITE_EX,
        'light-cyan': Fore.LIGHTCYAN_EX,
        'light-yellow': Fore.LIGHTYELLOW_EX,
    }
    print(colors[color] + st.BRIGHT + text + st.RESET_ALL)


def convert_csv_to_json(csv_path: str, json_path: str):
    with open(csv_path, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        content = list(reader)

    with open(json_path, mode='w', newline='', encoding='utf-8') as jsonfile:
        json.dump(content, jsonfile, ensure_ascii=False, indent=4)


def read_csv(csv_path: str):
    with open(csv_path, mode='r', newline='', encoding='utf-8') as csvfile:
        return list(csv.DictReader(csvfile))


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
            datefmt="%Y-%m-%d-%H:%M:%S", style='{')
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
