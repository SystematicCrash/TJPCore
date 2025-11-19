import re
from models.data_models import Task
from models.api_models import Scenario
from exceptions.custom_exceptions import DataValidationError


# Assiging Tasks Absolute Ids with DFS
def _assign_absolute_ids(task: Task, prefix: str) -> None:
    task.absolute_id = f"{prefix}.{task.id}" if prefix else task.id
    for child in task.sub_tasks_objs:
        _assign_absolute_ids(child, task.absolute_id)


# Finding task's abs id 
def _create_abs_id(task: Task, parts: list) -> list[str]:
    if task.parent:
        _create_abs_id(task.parent, parts)   
    parts.append(task.id) 
    return parts


# Removing additional time criterias when task has one of them (This is nessaccery, otherwise may cause tj3 errors)
def _removing_additional_time_criterias(task: Task):
    time_fields = [
        "start", "end", "minstart", "maxstart", "minend", 
        "maxend", "duration", "effort", "effortdone", 
        "effortleft", "length"
        ]
    if task.milestone:
        [setattr(task, f, None) for f in time_fields]

    elif getattr(task, "start") and getattr(task, "end"):
        [setattr(task, field, None) for field in time_fields if field not in ['start', 'end']]
        
    else:
        for field in time_fields:
            if getattr(task, field):
                [setattr(task, f, None) for f in time_fields if f != field]
                break


# Building a Breakdown Structure of Tasks 
def _task_leveling(task: Task, tasks: dict[str, Task]) -> bool:
    is_top_level_task = False
    if not task.parentId:
        is_top_level_task = True
    parent = tasks.get(task.parentId, None)
    if parent:
        parent.sub_tasks_objs.append(task)
        task.parent = parent
        _find_inherited_properties(task)
    return is_top_level_task


# Finding top level inherited properties with DFS 
def _find_inherited_properties(task: Task) -> None:
    if task.parent and task.parent.chargeset == task.chargeset:
        task.inherited_chargeset = True


# Converting task dependecies ids to absolute ids
def _convert_dependencies_to_absolute(tasks: dict[str, Task], task: Task) -> None:
        for i, dep_id in enumerate(task.depends):
            depends_on = tasks.get(dep_id)
            if depends_on:
                if not depends_on.absolute_id:
                    depends_on.absolute_id = '.'.join(_create_abs_id(depends_on, []))
                task.depends[i] = depends_on.absolute_id

    
# Sorting a dict of tasks by their keys 
def _sort_tasks_by_id(tasks: dict[str, Task]) -> dict[str, Task]:
    return dict(sorted(tasks.items(), key=lambda item: int(re.search(r'\d+', item[0]).group())))


# Effecting scenario changes in tasks
def _effect_scenario_changes(scenario: Scenario, tasks: dict[str, Task]):

    for new_task in scenario.tasks_to_add:
        if not new_task.id:
            raise DataValidationError(message="Scenario task defined without id!", status_code=422)
        if tasks.get(new_task.id):
            raise DataValidationError(message=f"Task with id = `{new_task.id}` already exist and cannot be added!", status_code=422)
        tasks[new_task.id] = new_task

    for updated_task in scenario.tasks_to_update:
        task = tasks.get(updated_task.id)
        if task:
            task.scenario_specific_obj = updated_task
        else:
            raise DataValidationError(message=f"Task with id = `{updated_task.id}` not found to update!", status_code=422)

    for removed_task in scenario.tasks_to_remove:
        tasks.pop(removed_task, None)
    

# Instanciating Tasks Objects With Json Documents 
def initialize_tasks(data: list, scenario: Scenario) -> list[Task]:
    tasks: dict[str, Task] = {}
    top_level_tasks = []
    
    tasks = {doc["_source"]["id"]: Task(json_document=doc) for doc in data}
    if scenario:
        _effect_scenario_changes(scenario, tasks)

    tasks = _sort_tasks_by_id(tasks)

    for task in tasks.values(): 
        if _task_leveling(task, tasks):
            top_level_tasks.append(task)
        _removing_additional_time_criterias(task)
        _convert_dependencies_to_absolute(tasks, task)
    
    return top_level_tasks
