from dataclasses import dataclass, field, fields
from decimal import Decimal


@dataclass
class Resource:
    id: str = ''
    name: str = ''
    chargeset: str = ''
    email: str = ''
    fail: str = ''
    managers: str = ''
    purge: str = ''
    shifts: str = ''
    warn: str = ''
    efficiency: float = 0
    leaveallowance: float = 0
    rate: Decimal = Decimal("0")
    flags: list[str] = field(default_factory=list[str])
    journalentry: list[dict] = field(default_factory=list[dict])
    booking: list[dict] = field(default_factory=list[dict])
    leaves: list[dict] = field(default_factory=list[dict])
    limits: dict = field(default_factory=dict)
    supplement: dict = field(default_factory=dict)
    vacation: list[dict] = field(default_factory=list[dict])
    workinghours: dict = field(default_factory=dict)
    resources: list[dict] = field(default_factory=list[dict])
    json_document: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.json_document:
            return
        source = self.json_document.get("_source", {})

        for f in fields(self):
            if not f.name in source:
                continue
            value = source[f.name]
            
            if f.name == 'charge':
                setattr(self, f.name, Decimal(str(value)))
            
            else:
                setattr(self, f.name, value)



def initialize_resources(data: list):
    resources = []
    for resource in data:
        resources.append(Resource(json_document=resource))
    return resources



        
