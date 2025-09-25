from helpers.utility import cast_string_fields_to_numeric_types
from helpers.io_helpers import get_config, read_csv


_NORMALIZATION_RULES = {
    "task": {"complete": lambda v: float(v.replace("%", "")),
             "cost": lambda v: float(v.replace(",", "."))},
    "resource": {"cost": lambda v: float(v.replace(",", "."))}
}


""" Normalizing reports result """
def _normalize_reports(reports: dict[str, list[dict]]) -> None:
    for report_name, data in reports.items():
        rules = _NORMALIZATION_RULES.get(report_name, {})
        for doc in data:
            for field, func in rules.items():
                doc[field] = func(doc[field])
            cast_string_fields_to_numeric_types(doc)
    

""" Read reports CSV results into a dictionary """
def _read_reports_csv() -> dict[str, list[dict]]:
    sources: dict = get_config("paths.reports.files")
    report_dir = get_config("paths.reports.dir")
    return {
        report_name: read_csv(f"{report_dir}/{file_name}.csv")
        for report_name, file_name in sources.items()
    }


""" Preparing reports data for index or api response """
def perpare_reports() -> dict[str, list[dict]]:
    reports_result = _read_reports_csv()

    _normalize_reports(reports_result)

    return reports_result