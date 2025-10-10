from fastapi.testclient import TestClient
from http_api.endpoints import app
from helpers.io_helper import get_config

client = TestClient(app)


def test_unauthorized_request_ignored():
    project_id = "project_id"
    response = client.post(
        f"/tjp-core/run/{project_id}",
        )
    assert response.status_code == 403



def test_generate_reports_with_wrong_project_id():
    project_id = "wrong_project_id"
    response = client.post(
        f"/tjp-core/run/{project_id}",
        headers={"Authorization": "Bearer " + get_config("api_key")}
        )
    assert response.status_code == 404
    assert response.json()["message"] == f"Project with id = ({project_id}) not found!"
