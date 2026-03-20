from fastapi import APIRouter, HTTPException
from starlette.responses import JSONResponse

from session_manager.models import ChatIteration
from session_manager.session_manager import SessionManager
from session_manager.session_repository import NoStorageRepository
from models import MessageRequest, StartResponse

router = APIRouter()

manager = SessionManager(NoStorageRepository())

@router.get("/healthcheck")
def healthcheck():
    return JSONResponse(status_code=200, headers={"Live": "true"}, content="Ok")


@router.post("/start", response_model=StartResponse)
def start():
    session = manager.create_session(client=None)

    return StartResponse(
        session_id=str(session.session_id)
    )


@router.post("/message")
def message(req: MessageRequest):
    try:
        session = manager.get_session(req.session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")

    response = f"Echo: {req.message}"

    session.add_chat_iteration(
        ChatIteration(

        )
    )

    return {"response": response}