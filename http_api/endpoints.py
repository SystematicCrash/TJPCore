import time
from main import main
from models.api_models import Scenario
from helpers.logging_helper import logger
from helpers.config_helper import get_config
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from helpers.io_helper import json_stream
from fastapi.templating import Jinja2Templates
from pathlib import Path

app = FastAPI()


# Check if request has the correct api key in header
def is_athenticated(token: str) -> bool:
    return token == ('Bearer ' + get_config('api_key'))


# project analyzing based on plan scenario
@app.post('/run/{project_id}')
async def generate_reports(request: Request, project_id: str):

    if not is_athenticated(request.headers.get("authorization")):
        return JSONResponse(content={'status' : 'fail', 'message' : 'Access Denied!'}, status_code=403)
    
    if not project_id:
        return JSONResponse(content={'status' : 'fail', 'message' : 'No project id specified!'}, status_code=400)
    
    start = time.time()
    try:
        await main(project_id)        
    except HTTPException as exp:
        logger(exp.detail, mode='error')
        return JSONResponse(content={'status' : 'fail', 'message' : exp.detail}, status_code=exp.status_code)
    
    duration = time.time() - start
    return JSONResponse(
        content={'status': 'success', 'message': 'Process finished!', 'duration': f'{duration:.2f}'},
        status_code=200
    )


# project analyzing based on custom scenario
@app.post("/scenario/{project_id}")
async def scenario_analyze(project_id: str, scenario: Scenario, request: Request):

    if not is_athenticated(request.headers.get("authorization")):
        return JSONResponse(content={'status': 'fail', 'message': 'Access Denied!'}, status_code=403)
    
    if not project_id:
        return JSONResponse(content={'status': 'fail', 'message': 'No project id specified!'}, status_code=400)
    
    start = time.time()
    try:
        result = await main(project_id, scenario=scenario)
        result = {'scenario_name': scenario.name, **result}
    except HTTPException as exp:
        logger(exp.detail, mode='error')
        return JSONResponse(content={'status': 'fail', 'message': exp.detail}, status_code=exp.status_code)
    
    duration = time.time() - start
    content = {'status': 'success', 'message': 'Process finished!', 'duration': f'{duration:.2f}', 'data': result}
    return StreamingResponse(content=json_stream(content), status_code=200, media_type="application/json")




# Presenting tjp file content as html content
@app.get("/show-tjp")
async def show_file_jinja(request: Request):
    templates = Jinja2Templates(directory="templates")
    file_path = Path(get_config('paths.tjp_output'))
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Tjp file not found!")
    
    with file_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()
    
    return templates.TemplateResponse("tjp_as_html.html", {"request": request, "lines": lines, "filename": file_path.name})
