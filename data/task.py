from dataclasses import dataclass, field, fields
from datetime import datetime


@dataclass
class Task:
    task_id: str = ''
    task_name: str = ''
    task_code: str = ''
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
    milestone: bool = False
    task_linking: list[str] = field(default_factory=list)
    resource_assignment: list[str] = field(default_factory=list)
    task_dependency: list[str] = field(default_factory=list)
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
                setattr(self, f.name, value)
        self.task_id = es_doc.get("_id", '')


# Generating tasks
def generate_tasks(tasks):
    tasks_objs: list[Task] = []
    for document in tasks:
        task = Task(es_doc=document)
        task.chargeset = task.task_id + "Costs"
        if task.milestone and task.task_start_date and task.task_end_date:
            task.task_end_date = None
        tasks_objs.append(task)

    return tasks_objs
