from dataclasses import dataclass, field, fields


@dataclass
class Scenario:
    id: str = ''
    name: str = ''
    active: bool = False
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



def initialize_scenarios(data: list):
    scenarios = []
    for scenario in data:
        scenarios.append(Scenario(json_document=scenario))
    return scenarios