import re
from colorama import Fore, Style as st


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


def cast_string_fields_to_numbers(data_set: dict):
    INTEGER_REGEX = r'^[+-]?\d+$'
    FLOAT_REGEX = r'^[+-]?(?:\d+\.\d*|\.\d+|\d+\.\d+)(?:[eE][+-]?\d+)?$'
    for item in data_set:
        for field, value in item.items():
            if not isinstance(value, str) or field in ['wbs', 'id']:
                continue
            if field == 'rate':
                value = value.replace(',', '.')
            if re.fullmatch(INTEGER_REGEX, value):
                item[field] = int(value)
            elif re.fullmatch(FLOAT_REGEX, value):
                item[field] = float(value)
    return data_set



