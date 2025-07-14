from dataclasses import dataclass, field, fields


@dataclass
class AccountReport:
    bsi: str = ''
    id: str = ''
    name : str = ''


    def initializing(self, data: dict):
        for f in fields(self):
            if f.name in data:
                setattr(self, f.name, data[f.name])


def generate_account_obj(accounts: list):
    accounts_objs = []
    for account in accounts:
        accounts_objs.append(AccountReport(**account))

    return accounts_objs