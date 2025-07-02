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
    # TODO Fix this booking property
    task_booking: str = ''
    charge: float = 0
    milestone: bool = False
    task_linking: list[str] = field(default_factory=list)
    resource_assignment: list[str] = field(default_factory=list)
    task_dependency: list[str] = field(default_factory=list)

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
    lines = ''
    for document in tasks:
        task_lines = []
        task = Task()
        task.initializing(document)
        account_name = task.task_id + "Costs"
        task_lines.append(f"account {account_name} \"{"costs of " + task.task_id}\"\n")

        task_lines.append(f"task {task.task_id} \"{task.task_name}\" {{")

        # milestone task just can have start or end date
        if task.milestone:
            task_lines.append("  milestone")

            if task.task_start_date:
                task_lines.append(f"  start {task.task_start_date}")

            elif task.task_end_date:
                task_lines.append(f"  end {task.task_end_date}")

        else:
            if task.task_start_date:
                task_lines.append(f"  start {task.task_start_date}")

            elif task.task_end_date:
                task_lines.append(f"  end {task.task_end_date}")

        # TODO When resource assigned
        # if task.task_effort > 0:
        #     task_lines.append(f"  effort {int(task.task_effort)}d")
        # if task.resource_assignment:
        #     task_lines.append(f"  allocate {','.join(task.resource_assignment)}")

        if task.task_dependency:
            task_lines.append(f"  depends {','.join(task.task_dependency)}")
            if task.dependency_type in ["onstart", "onend"]:
                task_lines.append(" {")
                task_lines.append(f"    {task.dependency_type}")
                task_lines.append(f"  gapduration {task.allowed_delay}")
                task_lines.append("  }")

        if task.constraint_date and task.constraint_type:
            if task.constraint_type == 'start_no_earlier_than':
                task_lines.append(f"  minstart {task.constraint_date}")

            if task.constraint_type == 'start_on_later_than':
                task_lines.append(f"  maxstart {task.constraint_date}")

            if task.constraint_type == 'finish_no_earlier_than':
                task_lines.append(f"  minend {task.constraint_date}")

            if task.constraint_type == 'finish_no_later_than':
                task_lines.append(f"  maxend {task.constraint_date}")

            if task.constraint_type == 'must_finish_on':
                task_lines.append(f"  minend {task.constraint_date}")
                task_lines.append(f"  maxend {task.constraint_date}")

            if task.constraint_type == 'must_start_on':
                task_lines.append(f"  minstart {task.constraint_date}")
                task_lines.append(f"  maxstart {task.constraint_date}")

        # TODO don't define this right now
        # if task.deadline:
        #     task_lines.append(f"  maxend {task.deadline}")

        if task.priority:
            task_lines.append(f"  priority {task.priority}")

        if task.task_linking:
            task_lines.append(f'  flags {task.task_linking}')

        task_lines.append(f"  chargeset {account_name}, ProjectCosts")

        # TODO implement shift property for exception working hours
        if task.task_cost:
            task_lines.append(f"  charge {task.charge} onend")

        task_lines.append(f"  note \"{task.summary_task}\"")

        task_lines.append("}")
        lines += "\n".join(task_lines)
        lines += "\n\n"
    return lines
