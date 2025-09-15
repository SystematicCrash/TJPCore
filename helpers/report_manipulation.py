from helpers.utility import cast_string_fields_to_numeric_types

def manipulation(reports: dict[str, list]):
    for report_name, data in reports.items():
        if report_name == "task":
            _tasks_reports_manipulation(data)
        elif report_name == "resource":
            _resources_reports_manipulation(data)
        cast_string_fields_to_numeric_types(data)


def _tasks_reports_manipulation(data: list[dict]):
    for doc in data:
        doc["complete"] = float(doc["complete"].replace("%", ""))  
        doc["cost"] = float(doc["cost"].replace(",", "."))



def _resources_reports_manipulation(data: list[dict]):
    for doc in data:
        doc["cost"] = float(doc["cost"].replace(",", "."))
