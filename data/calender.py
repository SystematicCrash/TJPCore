from dataclasses import dataclass, field, fields
from datetime import datetime
from utility import day_to_an_abbreviation


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
                setattr(self, f.name, value)
        self.calendar_id = es_doc.get("_id", '')


# Generating project calendar information
def generate_calendars(calendars):
    content = ''
    for document in calendars:
        calendar_lines = []
        calendar = Calender()
        calendar.initializing(document)

        calendar.working_days_exceptions.append("2025-08-02")
        calendar.working_days_exceptions.append("2025-08-03")

        if calendar.working_days and calendar.working_hours:
            calendar.working_days = day_to_an_abbreviation(calendar.working_days)
            calendar.working_hours = calendar.working_hours.replace("-", " - ")
            calendar_lines.append(f"  workinghours {calendar.working_days} {calendar.working_hours}")

        calendar_lines.append("}\n")

        if calendar.working_days_exceptions:
            exception_days = ",\nholiday \"Exception Day\"".join(calendar.working_days_exceptions)
            calendar_lines.append(f"leaves\nholiday \"Exception Day\" {exception_days}")

        content += "\n".join(calendar_lines)
        content += "\n\n"
    return content
