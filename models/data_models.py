from __future__ import annotations
from dataclasses import dataclass, field, fields
from decimal import Decimal
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



@dataclass
class Task:
    id: str = ''
    absolute_id: str = ''
    name: str = ''
    projectid: str = ''
    note: str = ''
    scheduling: str = ''
    responsible: str = ''
    parentId: str = ''
    scheduled: bool = False
    milestone: bool = False
    inherited_chargeset: bool = False
    priority: int = 0
    effort: float = 0
    effortdone: float = 0
    duration: float = 0
    effortleft: float = 0
    length: float = 0
    complete: float = 0
    charge: Decimal = Decimal("0")
    maxstart: date = None
    minstart: date = None
    maxend: date = None
    minend: date = None
    start: date = None
    end: date = None
    parent: Task = None
    scenario_specific_obj: "Task" = None
    subtasks: list[str] =   field(default_factory=list[str])
    sub_tasks_objs: list[Task] = field(default_factory=list)
    shifts: list[str] =     field(default_factory=list[str])
    chargeset: list[str] =  field(default_factory=list[str])
    flags: list[str] =      field(default_factory=list[str])
    depends: list[str] =    field(default_factory=list[str])
    precedes: list[str] =   field(default_factory=list[str])
    limits: dict =               field(default_factory=dict)
    allocate: list[str] =   field(default_factory=list[str])
    json_document: dict =        field(default_factory=dict)

    def __post_init__(self):
        if not self.json_document:
            return
        source = self.json_document.get("_source", {})

        for f in fields(self):
            value = source.get(f.name, None)
            if not value:
                continue
            if f.name == "charge":
                setattr(self, f.name, Decimal(str(value)))
            else:
                setattr(self, f.name, value)
    


@dataclass
class Resource:
    id: str = ''
    projectid: str = ''
    name: str = ''
    email: str = ''
    efficiency: float = 0
    leaveallowance: float = 0
    rate: Decimal = Decimal("0")
    scenario_specific_obj: "Resource" = None
    chargeset: list[str] = field(default_factory=list[str])
    shifts: list[str] = field(default_factory=list[str])
    managers: list[str] = field(default_factory=list[str])
    flags: list[str] = field(default_factory=list[str])
    leaves: list[dict] = field(default_factory=list[dict])
    limits: dict = field(default_factory=dict) 
    vacation: list[dict] = field(default_factory=list[dict])
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
            
            if f.name == 'charge':
                setattr(self, f.name, Decimal(str(value)))
            else:
                setattr(self, f.name, value)



@dataclass
class Scenario:
    id: str = ''
    name: str = ''
    active: bool = False
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



@dataclass
class Shift:
    id: str = ''
    name: str = ''
    projectid: str = ''
    replace: bool = False
    timezone: str = ''
    vacation: list[dict] = field(default_factory=list[dict])
    leaves: list[dict] = field(default_factory=list[dict])
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



@dataclass
class Account:
    id: str = ''
    name: str = ''
    projectid: str = ''
    aggregate: str = ''
    flags: list[str] = field(default_factory=list[str])
    credits: list[dict] = field(default_factory=list[dict])
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
