from dataclasses import dataclass, field, fields
from datetime import date, datetime

@dataclass
class Project:
    id: str = ''
    name: str = ''
    version: str = ''
    numberformat: str = ''
    outputdir: str = ''
    shorttimeformat: str = ''
    timeformat: str = ''
    timezone: str = ''
    currency: str = ''
    currencyformat: str = ''
    include: str = ''
    trackingscenario: str = ''
    start: date = None
    end: date = None
    markdate: date = None
    now: date = None
    dailyworkinghours: int = float
    timingresolution: int = 0
    yearlyworkingdays: int = 0
    duration: int = 0
    weekstartsmonday: bool = False
    weekstartssunday: bool = False
    alertlevels: dict = field(default_factory=dict)
    extend: dict = field(default_factory=dict)
    journalentry: list[dict] = field(default_factory=list[dict])
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

        date_format = "%Y-%m-%d"  

        self.start = datetime.strptime(self.start, date_format).date()
        self.end = datetime.strptime(self.end, date_format).date()

        self.duration = (self.end - self.start).days


def initialize_projects(data: list):
    projects = []
    for project in data:
        projects.append(Project(json_document=project))
    return projects


