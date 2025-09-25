import subprocess
from elasticsearch import AsyncElasticsearch
from http_api.models import Scenario
from helpers.elastic_helper import make_connection
from helpers.config_helper import get_config
from helpers.io_helpers import error_register
from exceptions.custom_exceptions import TJ3ProcessError
from pipline.data_collector import gather_project_data
from pipline.tj_builder import generate_tjp
from pipline.data_persister import indexing_reports
from pipline.data_normalizer import perpare_reports


""" Running taskjuggler project manager """
async def _run_tj3(connection: AsyncElasticsearch, output_path: str) -> None:
    result = subprocess.run(
        "tj3 " + output_path, shell=True, stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE, text=True, encoding='utf-8'
    )
    if result.returncode != 0:
        message = f"Failed to finish processing! Because of below errors:\n{result.stderr}"
        await error_register(connection, message)
        raise TJ3ProcessError(message, 500)


""" Processing """
async def main(project_id: str, scenario: Scenario = None) -> dict|None:
    connection = make_connection()

    data_map = await gather_project_data(connection, project_id)

    output_path = get_config("paths.tjp_output")

    generate_tjp(data_map, output_path, scenario)
    
    await _run_tj3(connection, output_path)

    reports_data = perpare_reports()

    if not scenario: # No need to indexing data in scenario mode
        await indexing_reports(connection, reports_data)
    else:
        return reports_data
    await connection.close()




