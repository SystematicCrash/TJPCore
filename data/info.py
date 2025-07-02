from dataclasses import dataclass, fields
from datetime import datetime
from deep_translator import GoogleTranslator


@dataclass
class ProjectInfo:
    project_id: str = ''
    project_name: str = ''
    project_type: str = ''
    start_date: str = ''
    end_date: str = ''
    project_duration: int = 0
    timezone: str = ''
    status_date: str = ''
    calendar_type: str = ''
    financial_unit: str = ''
    calendar_start: str = ''
    planned_start_date: str = ''
    number_of_floors: int = 0
    project_location: str = ''
    project_address: str = ''
    supervisor: str = ''
    architect_designer: str = ''
    structural_designer: str = ''
    mechanical_designer: str = ''
    electrical_designer: str = ''
    project_cost: float = 0
    project_manager: str = ''
    baseline: str = ''
    baseline_cost: float = 0
    baseline_fixed_cost: float = 0

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
        self.project_id = es_doc.get('_id')


# Generating project info at the top
def generate_project_info(info):
    content = ''
    for document in info:
        info_lines = []
        info = ProjectInfo()
        info.initializing(document)
        project_name = GoogleTranslator(source="fa", target="en").translate(info.project_name)

        info_lines.append(
            f"project {info.project_id} \"{project_name}\" {info.start_date} +{info.project_duration}d {{")
        info_lines.append(f"  timezone \"{info.timezone}\"")

        if info.financial_unit == 'ریال':
            info_lines.append(f"  currency \"IRR\"")
        else:
            info_lines.append(f"  currency \"{info.financial_unit}\"")

        info_lines.append(f"  now {info.status_date}")

        content += '\n'.join(info_lines)
        content += '\n'
    return content
