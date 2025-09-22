from pydantic import BaseModel
from typing import Any, Dict


""" Scenario model class """
class Scenario(BaseModel):
    name: str
    body: Dict[str, Any]
