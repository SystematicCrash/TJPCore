from dataclasses import dataclass, field, fields


@dataclass
class Shift:
    id: str = ''
    name: str = ''
    replace: bool = False
    timezone: str = ''
    vacations: list[dict] = field(default_factory=list[dict])
    leaves: list[dict] = field(default_factory=list[dict])
    workinghours: dict = field(default_factory=dict)
    shifts: list[dict] = field(default_factory=list[dict])
    json_document: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.json_document:
            return

        source = self.json_document.get("_source", {})

        for f in fields(self):
            if not f.name in source:
                continue

            value = source[f.name]
            setattr(self, f.name, value)



def initialize_shifts(data: list):
    shifts = []
    for shift in data:
        shifts.append(Shift(json_document=shift))
    return shifts