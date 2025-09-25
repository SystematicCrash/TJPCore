from pydantic import BaseModel
from typing import Optional
from pydantic.dataclasses import dataclass as pydantic_dataclass
from models.data_models import Resource, Task



@pydantic_dataclass
class Resource(Resource):
    pass


@pydantic_dataclass
class Task(Task):
    pass


# Scenario model 
class Scenario(BaseModel):
    name: str
    description: Optional[str] = ""
    resources_to_update: Optional[list[Resource]] = []
    tasks_to_update: Optional[list[Task]] = []
    resources_to_add: Optional[list[Resource]] = []
    tasks_to_add: Optional[list[Task]] = []
    resources_to_remove: Optional[list[str]] = []
    tasks_to_remove: Optional[list[str]] = []
