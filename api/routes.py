from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from models.schemas import UserInput, CollectedData, ErrorResponse
from langgraph_logic.workflow import run_workflow
from langgraph_logic.utils import error_response

router = APIRouter()

@router.post("/collect")
async def collect(request: Request):
    try:
        body = await request.json()
        if not isinstance(body, dict):
            return error_response("Request body must be a JSON object", status.HTTP_400_BAD_REQUEST)
        user_id = body.get("user_id")
        user_input = body.get("user_input")
        if not user_id:
            return error_response("user_id is required", status.HTTP_400_BAD_REQUEST)
        result = run_workflow(user_id, user_input)
        return JSONResponse(content=result)
    except Exception as e:
        return error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)
