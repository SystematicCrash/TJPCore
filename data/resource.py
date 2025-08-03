from __future__ import annotations
from dataclasses import dataclass, field, fields
from datetime import datetime

from exceptions.custom_exceptions import DataValidationError
from helpers.utility import day_to_an_abbreviation


def _format_allow_leaves(resource: Resource):
    if not resource.allowed_leave:
        return
    number = str(''.join(list(filter(lambda x: x.isdigit(), resource.allowed_leave))))
    interval = 'd' if (resource.allowed_leave.__contains__("day")) \
        else ('w' if (resource.allowed_leave.__contains__("week")) else 'm')
    resource.allowed_leave = number + interval


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

    def initializing(self, es_doc: dict):
        source = es_doc.get("_source", {})
        for f in fields(self):
            if f.name in source:
                value = source[f.name]
                if value and f.name.endswith('_date') and isinstance(value, str):
                    try:
                        datetime.strptime(value, '%Y-%m-%d')
                    except ValueError:
                        raise DataValidationError("Invalid date format:" + value, 500)
                setattr(self, f.name, value)
        self.resource_id = es_doc.get("_id", '')
        _format_allow_leaves(self)




# Generating resources
def generate_resources(resources: list, types: set):
    parent_resources = []
    for resource_type in types:
        parent_res = {'id': resource_type, 'name': 'resources of type ' + resource_type, 'flags': [resource_type],
                      'child_resources': []}
        for doc in resources:
            if doc['_source']['resource_type'] == resource_type:
                resource = Resource(es_doc=doc)
                resource.unavailability_date = '2025-08-06' # TODO remove this later
                resource.working_days = day_to_an_abbreviation(resource.working_days)
                parent_res['child_resources'].append(resource)
        parent_resources.append(parent_res)
    return parent_resources
