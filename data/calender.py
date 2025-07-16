from dataclasses import dataclass, field, fields
from datetime import datetime
from helpers.utility import day_to_an_abbreviation
from sys import exit

@dataclass
class Calender:
    calendar_id: str = ''
    project_calendar: str = ''
    working_hours: str = ''
    non_working_hours: str = ''
    working_days: str = ''
    non_working_days: str = ''
    working_days_exceptions: list[str] = field(default_factory=list)
    working_hours_exceptions: list[str] = field(default_factory=list)
    important_dates: list[str] = field(default_factory=list)
    es_doc: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.es_doc:
            self.initializing(self.es_doc)

    def initializing(self, es_doc: dict):
        source = es_doc.get("_source", {})
        for f in fields(self):
            if f.name in source:
                value = source[f.name]
                if value and f.name.endswith('_date') and isinstance(value, str):
                    try:
                        datetime.strptime(value, '%Y-%m-%d')
                    except ValueError:
                        print("Invalid date format:", value)
                        exit(1)
                setattr(self, f.name, value)
        self.calendar_id = es_doc.get("_id", '')


# Generating project calendar information
def generate_calendars(calendars):
    calendars_objs = []
    for doc in calendars:
        calendar = Calender(es_doc=doc)
        calendar.working_days_exceptions.append("2025-08-02") # TODO remove these later
        calendar.working_days_exceptions.append("2025-08-24")
        calendar.working_days = day_to_an_abbreviation(calendar.working_days)
        calendars_objs.append(calendar)
    return calendars_objs[0] if len(calendars_objs) != 0 else Calender()