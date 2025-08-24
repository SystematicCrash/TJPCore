from dataclasses import dataclass, field, fields
from decimal import Decimal
from datetime import date



@dataclass
class Task:
    id: str = ''
    name: str = ''
    projectid: str = ''
    note: str = ''
    scheduling: str = ''
    responsible: str = ''
    schedulingmode: str = ''
    shifts: str = ''
    fail: str = ''
    warn: str = ''
    adopt: str = ''
    chargeset: str = ''
    depends: str = ''
    purge: str = ''
    precedes: str = ''
    scheduled: bool = False
    milestone: bool = False
    priority: int = 0
    effort: float = 0
    effortdone: float = 0
    duration: float = 0
    effortleft: float = 0
    length: float = 0
    complete: float = 0
    maxstart: date = None
    minstart: date = None
    maxend: date = None
    minend: date = None
    strat: date = None
    end: date = None
    charge: Decimal = Decimal("0")
    flags: list[str]  = field(default_factory=list[str])
    booking: list[dict] = field(default_factory=list[dict])
    limits: dict = field(default_factory=dict)
    journalentry: list[dict] = field(default_factory=list[dict])
    priod: dict = field(default_factory=dict)
    allocate: list[dict] = field(default_factory=list[dict])
    supplement: dict = field(default_factory=dict)
    tasks: list[dict] = field(default_factory=list[dict])
    json_document: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.json_document:
            return
        source = self.json_document.get("_source", {})

        for f in fields(self):
            if not f.name in source:
                continue
            value = source[f.name]

            if f.name == "charge":
                setattr(self, f.name, Decimal(str(value)))
            
            else:
                setattr(self, f.name, value)

    


def initialize_tasks(data: list):
    tasks = []
    for task in data:
        tasks.append(Task(json_document=task))
    return tasks



        



