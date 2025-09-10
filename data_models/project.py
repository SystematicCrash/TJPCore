from dataclasses import dataclass, field, fields
from datetime import date
from helpers.utility import time_unit_to_an_abbreviation

@dataclass
class Project:
    id: str = ''
    name: str = ''
    timezone: str = ''
    currency: str = ''
    trackingscenario: str = ''
    start: date = None
    markdate: date = None
    now: date = None
    dailyworkinghours: float = 0
    yearlyworkingdays: float = 0
    duration: int = 0
    duration_unit: str = ''
    weekstartsmonday: bool = False
    weekstartssunday: bool = False
    workinghours: dict = field(default_factory=dict)
    json_document: dict = field(default_factory=dict)


    def __post_init__(self):
        if not self.json_document:
            return

        source = self.json_document.get("_source", {})
        for f in fields(self):
            if not f.name in source:
                continue
            value = source[f.name]
            setattr(self, f.name, value)
        self.duration_unit = time_unit_to_an_abbreviation(self.duration_unit)




def initialize_projects(data: list):
    projects = []
    for project in data:
        projects.append(Project(json_document=project))
    return projects


