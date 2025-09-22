import time
import main
from http_api.models import Scenario
from helpers.io_helpers import logger
from helpers.config_helper import get_config
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse


app = FastAPI()



""" Check if request has the correct api key in header """
def is_athenticated(header: str) -> bool:
    token = 'Bearer ' + get_config('api_key')
    return header == token


""" Start project analyzing """
@app.post('/tjp-core/run/{project_id}')
async def run(request: Request, project_id: str):
    if not is_athenticated(request.headers.get("authorization")):
        return JSONResponse(content={'status' : 'fail', 'message' : 'Access Denied!'}, status_code=403)
    
    if not project_id:
        return JSONResponse(content={'status' : 'fail', 'message' : 'No project id specified!'}, status_code=400)
    
    start = time.time()
    try:
        await main.main(project_id)        
    except HTTPException as exp:
        logger(exp.detail,mode='error', console=False)
        return JSONResponse(content={'status' : 'fail', 'message' : exp.detail}, status_code=exp.status_code)
    duration = time.time() - start
    return JSONResponse(
        content={
            'status': 'success', 
            'message': 'Process finished!', 
            'duration': f'{duration:.2f}'
        }, status_code=200)



@app.post("/tjp-core/scenario/{project_id}")
async def scenario_analyze(project_id: str, scenario: Scenario, request: Request):
    if not is_athenticated(request.headers.get("authorization")):
        return JSONResponse(
            content={'status': 'fail', 'message': 'Access Denied!'},
            status_code=403
    )
    if not project_id:
        return JSONResponse(
            content={'status': 'fail', 'message': 'No project id specified!'},
            status_code=400
    )
    start = time.time()
    try:
        result = await main.main(project_id, scenario=scenario)
        result['tasks'] = result['task']
        result['resources'] = result['resource']
        del result['task'], result['resource']
    except HTTPException as exp:
        return JSONResponse(
            content={'status': 'fail', 'message': exp.detail},
            status_code=exp.status_code
    )
    duration = time.time() - start
    return JSONResponse(
        content={
            'status': 'success',
            'message': 'Process finished!',
            'duration': f'{duration:.2f}',
            'data': result
        },
        status_code=200
    )


