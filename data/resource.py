from dataclasses import dataclass, field, fields
from datetime import datetime
from data.utility import day_to_an_abbreviation
import re


@dataclass
class Resource:
    resource_id: str = ''
    resource_name: str = ''
    resource_type: str = ''
    max_units: int = 0
    resource_capacity_per_task: int = 0
    base_cost: float = 0
    overtime_cost: float = 0
    cost_per_use: float = 0
    total_resource_cost: float = 0
    cost_calculation_method: str = ''
    availability_date: str = ''
    working_hours: str = ''
    working_days: str = ''
    working_hours_change: str = ''
    unavailability_date: str = ''
    allowed_leave: str = ''
    actual_cost: float = 0
    base_calendar: str = ''
    resource_group: str = ''
    accrue_at: str = ''
    cost_center: str = ''
    cost_increase_per_time_unit: int = 0
    enterprise: bool = False
    enterprise_team_member: str = ''
    es_doc: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.es_doc:
            self.initializing(self.es_doc)
            self.format_allow_leaves()

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
        self.resource_id = es_doc.get("_id", '')


    def format_allow_leaves(self):
        if not self.allowed_leave:
            return
        number = str(''.join(list(filter(lambda x: x.isdigit(), self.allowed_leave))))
        interval = 'd' if (self.allowed_leave.__contains__("day")) \
            else ('w' if (self.allowed_leave.__contains__("week")) else 'm')
        self.allowed_leave = number + interval


# Generating resources
def generate_resources(resources, types: set):
    parent_resources = []
    for resource_type in types:
        parent_res = {}
        parent_res['id'] = resource_type
        parent_res['name'] = 'resources of type ' + resource_type
        parent_res['flags'] = [resource_type]
        parent_res['child_resources'] = []
        for doc in resources:
            if doc['_source']['resource_type'] == resource_type:
                resource = Resource(es_doc=doc)
                resource.working_days = day_to_an_abbreviation(resource.working_days)
                parent_res['child_resources'].append(resource)
        parent_resources.append(parent_res)

    return parent_resources
