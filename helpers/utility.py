import re
import sys
import time
from colorama import Fore, Style as st
from colorama import Style
from tqdm import tqdm


def sort_weekdays(days: list[str]) -> list[str]:
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    order_map = {day: i for i, day in enumerate(order)}
    return sorted(days, key=lambda d: order_map[d])


def day_to_an_abbreviation(days: list):
    return [(day[:3]).lower() for day in days]


def time_unit_to_an_abbreviation(unit: str):
    if unit in ["months", "minutes"]:
        return unit[:3]
    elif unit in ["days", "years", "weeks"]:
        return unit[:3]


def colorized_print(color: str, text: str, tqdm_write=True):
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
    if color in colors:
        if tqdm_write:
            from tqdm import tqdm
            tqdm.write(colors[color] + st.DIM +  text + st.RESET_ALL)
        else:
            print(colors[color] + st.DIM +  text + st.RESET_ALL)
    else:
        raise ValueError(f"{color} is not present in colors")


def cast_string_fields_to_numeric_types(data_set: dict):
    INTEGER_REGEX = r'^[+-]?\d+$'
    FLOAT_REGEX = r'^[+-]?(?:\d+\.\d*|\.\d+|\d+\.\d+)(?:[eE][+-]?\d+)?$'
    for field, value in data_set.items():
        if not isinstance(value, str) or field in ['wbs', 'id']:
            continue
        if field == 'rate':
            value = value.replace(',', '.')
        if re.fullmatch(INTEGER_REGEX, value):
            data_set[field] = int(value)
        elif re.fullmatch(FLOAT_REGEX, value):
            data_set[field] = float(value)
    return data_set


end_of_process = False
progress = 0


def animate_processing():
    global progress, end_of_process
    dots = 0
    direction = 1
    while not end_of_process:
        dot_str = "." * dots + " " * (5 - dots)
        message = f"\r{Fore.LIGHTCYAN_EX}Processing{dot_str}{Style.DIM}"
        print(message, end="")
        sys.stdout.flush()
        time.sleep(0.3)
        dots += direction
        if dots == 5 or dots == 0:
            dots = 0


def progress_bar():
    global progress, end_of_process
    with tqdm(total=1000, desc="Progress", unit="step", file=sys.stdout) as pbar:
        last = 0
        while not end_of_process:
            pbar.update(progress - last)
            last = progress
            time.sleep(0.1)
        pbar.update(100 - last)
