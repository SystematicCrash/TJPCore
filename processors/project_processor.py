from models.data_models import Project


def initialize_projects(data: list):
    projects = []
    for project in data:
        projects.append(Project(json_document=project))
    return projects
