from dataclasses import dataclass, field, fields
from datetime import datetime
from helpers.utility import colorized_print
from helpers.io_helpers import logger
from deep_translator import GoogleTranslator
from sys import exit

@dataclass
class ProjectInfo:
    project_id: str = ''
    project_name: str = ''
    project_type: str = ''
    start_date: str = ''
    end_date: str = ''
    project_duration: int = 0
    timezone: str = ''
    status_date: str = ''
    calendar_type: str = ''
    financial_unit: str = ''
    calendar_start: str = ''
    planned_start_date: str = ''
    number_of_floors: int = 0
    project_location: str = ''
    project_address: str = ''
    supervisor: str = ''
    architect_designer: str = ''
    structural_designer: str = ''
    mechanical_designer: str = ''
    electrical_designer: str = ''
    project_cost: float = 0
    project_manager: str = ''
    baseline: str = ''
    baseline_cost: float = 0
    baseline_fixed_cost: float = 0
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
        self.project_id = es_doc.get('_id')


# Generating project info objects
def generate_project_info(info):
    info_objs = []
    for doc in info:
        info = ProjectInfo(es_doc=doc)
        try:
            info.project_name = GoogleTranslator(source="fa", target="en").translate(info.project_name)
        except Exception as e:
            message = "\nFailed to connect to Google Translator! used for project name translation"
            colorized_print('red', message)
            logger(message, 'error', console=False)
        info_objs.append(info)
    return info_objs[0] if len(info_objs) != 0 else ProjectInfo()