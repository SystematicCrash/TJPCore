from __future__ import annotations
from dataclasses import dataclass, field, fields
from datetime import datetime
from sys import exit
import re


# Check if task has a parent ? that's mean current task is a subtask of the other task
def _has_parent(task_code: str) -> bool:
    code = task_code.replace('.', '')
    return len(code) == 1



# Finding task parent ID
def _find_parent_id(task_id: str):
    code = ''.join(re.findall(r'\d+', task_id))
    if len(code) == 1:
        return None
    if len(code) == 2:
        return 'task_' + code[0]
    else:
        code = code[:2]
        return 'task_' + '_'.join(code)


# Identifying task level. level-one = top-level, level-two = mid-level, level-three = low-level
def _find_level(task_code: str):
    code = task_code.replace('.', '')
    if len(code) == 1:
        return 1
    elif len(code) == 2:
        return 2
    elif len(code) == 3:
        return 3
    return -1


# Defining current task as a subtask of it's parent and considering inherited values from parent
def link_to_parent(parent: Task, task: Task):
    if not parent:
        return
    if parent.chargeset:
        task.inherited_chargeset = True
    if parent.task_linking == task.task_linking:
        task.inherited_task_linking = True
    if parent.priority == task.priority:
        task.inherited_priority = True
    # if parent.resource_assignment == task.resource_assignment:
    #     task.inherited_resource_assignment = True
    if parent.task_dependency == task.task_dependency:
        task.inherited_dependencies = True
    parent.children.append(task)


# Converting actual IDs to absolutes, task_3_1_2 --> task_3.task_3_1_1.task_3_1_2
def _convert_dependencies_ids_to_absolute(task_dependency: list):
    if not task_dependency:
        return []
    absolute_dependencies_ids = set()
    for dependency_id in task_dependency:
        parents = []
        parent_id = _find_parent_id(dependency_id)
        if not parent_id:
            continue
        parents.append(parent_id)
        while True:
            parent_id = _find_parent_id(parent_id)
            if not parent_id:
                break
            parents.append(parent_id)
        absolute_dependencies_ids.add('.'.join(parents[::-1]) + '.' + dependency_id)
    return list(absolute_dependencies_ids)


@dataclass
class Task:
    task_level: int = 0
    task_parent_id: str = ''
    task_id: str = ''
    task_name: str = ''
    task_code: str = ''
    sorting_code: int = 0
    task_type: str = ''
    summary_task: str = ''
    calender_task_duration: int = 0
    work_duration: int = 0
    task_start_date: str = ''
    task_end_date: str = ''
    task_effort: int = 0
    dependency_type: str = ''
    allowed_delay: int = 0
    shifts: str = ''
    constraint_type: str = ''
    constraint_date: str = ''
    deadline: str = ''
    assignment_owner: str = ''
    assignment_units: int = ''
    resource_calendar: str = ''
    priority: int = 0
    task_cost: float = ''
    pending_status_team: str = ''
    periodic_task_start_date: str = ''
    periodic_task_settings: str = ''
    initial_estimated_cost: float = 0
    estimated_work: int = 0
    planned_deliverable_start: str = ''
    planned_deliverable_end: str = ''
    baseline_fixed_cost_accrual: str = ''
    task_booking: str = ''
    charge: float = 0
    chargeset: str = ''
    complete: int = 0
    milestone: bool = False
    inherited_task_linking: bool = False
    inherited_chargeset: bool = False
    inherited_dependencies: bool = False
    inherited_resource_assignment: bool = False
    inherited_priority: bool = False
    task_linking: list[str] = field(default_factory=list)
    task_dependency: list[str] = field(default_factory=list)
    resource_assignment: list[str] = field(default_factory=list)
    children: list = field(default_factory=list)
    es_doc: dict = field(default_factory=dict)

    # Called after __init__
    def __post_init__(self):
        if self.es_doc:
            self.initializing(self.es_doc)


    # Initialing class fields with elastic document values
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
        self.__reformations()

    def __reformations(self):
        self.task_level = _find_level(self.task_code)
        self.task_parent_id = _find_parent_id(self.task_id)
        self.task_dependency = _convert_dependencies_ids_to_absolute(self.task_dependency)
        self.sorting_code = int(self.task_code.replace(".", ""))
        self.chargeset = self.task_id + "Costs" # task unique account ID
        # If task is milestone and has start and end, then we don't need the end
        if self.milestone and self.task_start_date and self.task_end_date:
            self.task_end_date = ''
        if self.milestone or (self.task_start_date and self.task_end_date):
            self.work_duration = 0



# Generating task objects
def generate_tasks(tasks):
    # { level : { task_1 : obj1, task_2 : obj2 ... } }
    tasks_objs: dict[int, dict[str, Task]] = dict()
    for i in range(1, 4):
        tasks_objs[i] = {}
    for document in tasks:
        task = Task(es_doc=document)
        tasks_objs[task.task_level][task.task_id] = task
    # Sorting tasks
    for key, inner_dict in tasks_objs.items():
        sorted_inner = dict(sorted(inner_dict.items(), key=lambda item: item[1].sorting_code))
        tasks_objs[key] = sorted_inner
    # Creating tasks hierarchical structure
    for level in range(2, 4):
        for task in tasks_objs[level].values():
            if task.task_parent_id:
                link_to_parent(tasks_objs.get(task.task_level - 1, {}).get(task.task_parent_id), task)

    for level, inner_dict in tasks_objs.items():
        for id, task in inner_dict.items():
            if task.children:
                task.resource_assignment = []

    return tasks_objs.get(1).values()
