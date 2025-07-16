from dataclasses import dataclass, fields, field


@dataclass
class ResourceReport:
    bsi: str = ''
    id: str = ''
    name: str = ''
    base_cost: float = 0
    actual_cost: float = 0
    rate: float = 0
    accrue_at: str = ''
    overtime_cost: float = 0
    efficiency: int = 0
    type: str = ''
    availability: str = ''
    resource_group: str = ''
    es_doc: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.es_doc:
            self.initializing(self.es_doc)

    def initializing(self, data: dict):
        for f in fields(self):
            if f.name in data:
                setattr(self, f.name, data[f.name])



def generate_resources_reports(resources: list):
    resources_objs = []
    for resource in resources:
        resources_objs.append(ResourceReport(es_doc=resource))
    return resources_objs





