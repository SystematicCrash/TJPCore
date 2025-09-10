from __future__ import annotations
import re
from dataclasses import dataclass, field, fields
from decimal import Decimal
from datetime import date



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
    start_date: date = None
    end_date: date = None
    parent: Task = None
    subtasks: list[str] = field(default_factory=list[str])
    sub_tasks_objs: list[Task] = field(default_factory=list)
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
            value = source.get(f.name, None)
            if not value:
                continue
            if f.name == "charge":
                setattr(self, f.name, Decimal(str(value)))
            else:
                setattr(self, f.name, value)
    
            

""" Assiging Tasks Absolute Ids with DFS """
def assign_absolute_ids(task: Task, prefix: str):
    task.absolute_id = f"{prefix}.{task.id}" if prefix else task.id
    for child in task.sub_tasks_objs:
        assign_absolute_ids(child, task.absolute_id)



""" Building a Breakdown Structure of Tasks """
def find_parent(tasks: dict[str, Task], task: Task):
    if not task.parentId:
        return
    parent = tasks.get(task.parentId, None)
    if not parent:
        return
    parent.sub_tasks_objs.append(task)
    task.parent = parent



""" Removing top level inherited properties from tasks with DFS """
def remove_inherited_properties(task: Task):
    if task.parent and task.parent.chargeset:
        task.chargeset = [
            cs for cs in task.chargeset 
            if not cs in task.parent.chargeset
        ]
    for child in task.sub_tasks_objs:
        remove_inherited_properties(child)



""" Converting task dependecies ids to absolute ids """
def convert_dependencies_to_absolute(tasks: dict[str, Task], task: Task):
        for i, dep_id in enumerate(task.depends):
            depends_on = tasks.get(dep_id)
            if depends_on:
                task.depends[i] = depends_on.absolute_id


""" Sorting a list of tasks """
def sort_tasks_list_by_id(tasks: list[Task]):
    return list(sorted(tasks, key=lambda task: int(re.search(r'\d+', task.id).group())))


""" Sorting a dict of tasks by their keys """
def sort_tasks_dict_by_id(tasks: dict[str, Task]):
    return dict(sorted(tasks.items(), key=lambda item: int(re.search(r'\d+', item[0]).group())))


""" Instanciating Tasks Objects With Json Documents """
def initialize_tasks(data: list):
    tasks: dict[str, Task] = {}
    top_level_tasks = []
    
    tasks = {doc["_source"]["id"]: Task(json_document=doc) for doc in data}

    for task in tasks.values():
        find_parent(tasks, task)


    
    tasks = sort_tasks_dict_by_id(tasks)
    
    for task in tasks.values():
        if task.parent:
            continue
        top_level_tasks.append(task)
        assign_absolute_ids(task, '')
        remove_inherited_properties(task)
        task.sub_tasks_objs = sort_tasks_list_by_id(task.sub_tasks_objs)
            
    for task in tasks.values():
        convert_dependencies_to_absolute(tasks, task)
    

    return top_level_tasks