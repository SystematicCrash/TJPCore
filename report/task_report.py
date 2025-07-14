from dataclasses import dataclass, field, fields


@dataclass
class TaskReport:
    bsi: str = ''
    task_id: str = ''
    task_name: str = ''
    start: str = ''
    end: str = ''
    min_start: str = ''
    max_start: str = ''
    min_end: str = ''
    max_end: str = ''
    deadline: str = ''
    duration: str = ''
    effort: str = ''
    priority: str = ''
    completed: int = 0
    sub_tasks: list = field(default_factory=list)
    resources: list = field(default_factory=list)


    def initializing(self, data: dict):
        for f in fields(self):
            if f.name in data:
                setattr(self, f.name, data[f.name])



def generate_tasks_obj(tasks:list):
    tasks_objs = []
    for task in tasks:
        tasks_objs.append(TaskReport(**task))
    return tasks_objs

