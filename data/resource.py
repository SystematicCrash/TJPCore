from dataclasses import dataclass, fields
from datetime import datetime
from utility import day_to_an_abbreviation


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


# Generating resources
def generate_resources(resources, types: set):
    content = ''
    body: dict[str:list] = {}
    for resource_type in types:
        body[resource_type] = []

    for document in resources:
        resource = Resource()
        resource.initializing(document)

        if resource.resource_type in types:
            section = body[resource.resource_type]
            if not section:
                section.append(
                    f"resource {resource.resource_type} \"For resources of type {resource.resource_type}\" {{")

            section.append(f"  resource {resource.resource_id} \"{resource.resource_name}\" {{")

            if resource.max_units:
                section.append(f"    efficiency {resource.max_units}")

            if resource.base_cost and resource.cost_calculation_method:
                section.append(f"    rate {resource.base_cost} {resource.cost_calculation_method}")

            if resource.overtime_cost:
                section.append(f"    rate.overtime {resource.overtime_cost}")

            if resource.working_days and resource.working_hours:
                resource.working_days = day_to_an_abbreviation(resource.working_days)
                resource.working_hours = resource.working_hours.replace('-', ' - ')
                section.append(f"    workinghours {resource.working_days} {resource.working_hours}")

            if resource.resource_group:
                section.append(f"    flags {resource.resource_group}")

            if resource.cost_center:
                section.append(f"    chargeset {resource.cost_center}")

            section.append("  }\n")

    for section in body.keys():
        if body[section]:
            body[section].append("}")
            content += "\n".join(body[section])
            content += "\n"

        content += "\n\n"
    return content
