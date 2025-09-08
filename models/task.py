from dataclasses import dataclass, field, fields
from decimal import Decimal
from datetime import date
from typing import List



@dataclass
class Task:
    id: str = ''
    name: str = ''
    projectid: str = ''
    note: str = ''
    scheduling: str = ''
    responsible: str = ''
    parentId: str = ''
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
    start_date: date = None
    end_date: date = None
    charge: Decimal = Decimal("0")
    subtasks: list[str] = field(default_factory=list[str])
    sub_tasks_objs: List["Task"] = field(default_factory=list)
    shifts: list[str] = field(default_factory=list[str])
    chargeset: list[str] = field(default_factory=list[str])
    flags: list[str]  = field(default_factory=list[str])
    depends: list[str] = field(default_factory=list[str])
    precedes: list[str] = field(default_factory=list[str])
    limits: dict = field(default_factory=dict)
    allocate: list[dict] = field(default_factory=list[dict])
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
    top_level_tasks = []
    for task in data:
        tasks.append(Task(json_document=task))

    for task in tasks:
        if task.parentId:
            parent = [t for t in tasks if t.id == task.parentId][0]
            parent.sub_tasks_objs.append(task)
        
    top_level_tasks = [task for task in tasks if not task.parentId]
    return top_level_tasks