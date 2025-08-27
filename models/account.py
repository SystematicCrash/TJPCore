from dataclasses import dataclass, field, fields


@dataclass
class Account:
    id: str = ''
    name: str = ''
    projectid: str = ''
    aggregate: str = ''
    flags: list[str] = field(default_factory=list[str])
    credits: list[dict] = field(default_factory=list[dict])
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




def initialize_accounts(data: list):
    accounts = []
    for account in data:
        accounts.append(Account(json_document=account))
    return accounts

