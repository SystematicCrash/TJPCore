import re
from models.data_models import Resource
from models.api_models import Scenario
from exceptions.custom_exceptions import DataValidationError



# Effecting scenario changes in resources
def _effect_scenario_changes(scenario: Scenario, resources: dict[str, Resource]):

    for new_resource in scenario.resources_to_add:
        if not new_resource.id:
            raise DataValidationError(message="Scenario resource defined without id!", status_code=422)
        if resources.get(new_resource.id):
            raise DataValidationError(message=f"Resource with id = `{new_resource.id}` already exist and cannot be added!", status_code=422)
        resources[new_resource.id] = new_resource

    for updated_rsource in scenario.resources_to_update:
        resource = resources.get(updated_rsource.id)
        if resource:
            resource.scenario_specific_obj = updated_rsource
        else:
            raise DataValidationError(message=f"Resource with id = `{updated_resource.id}` not found to update!", status_code=422)

    for removed_resource in scenario.resources_to_remove:
        resources.pop(removed_resource, None)
    



def initialize_resources(data: list, scenario: Scenario) -> list[Resource]:
    resources: dict[str, Resource] = {}
    for resource in data:
        resources[resource["_source"]["id"]] = Resource(json_document=resource)
    if scenario:
        _effect_scenario_changes(scenario, resources)
    resources = dict(sorted(resources.items(), key=lambda item: int(re.search(r'\d+', item[0]).group())))


    return resources.values()
