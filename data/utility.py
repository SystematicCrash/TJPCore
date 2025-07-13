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
        'blue': Fore.BLUE, 'red': Fore.RED, 'cyan': Fore.CYAN,
        'yellow': Fore.YELLOW, 'white': Fore.WHITE, 'green' : Fore.GREEN,
        'light-blue' : Fore.LIGHTBLUE_EX, 'light-green' : Fore.LIGHTGREEN_EX}
    print(colors[color] + st.BRIGHT + text + st.RESET_ALL)

