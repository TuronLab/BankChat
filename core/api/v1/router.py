import os

from fastapi import APIRouter, HTTPException
from starlette.responses import JSONResponse

from config import ASSETS_PATH
from core.session_manager.models import ChatMessage
from core.session_manager.session_manager import SessionManager
from core.session_manager.session_repository import NoStorageRepository
from core.utils import read_markdown
from models import Response

router = APIRouter()

manager = SessionManager(NoStorageRepository())

@router.get("/healthcheck")
def healthcheck():
    return JSONResponse(status_code=200, headers={"Live": "true"}, content="Ok")


@router.get("/config")
def get_conf():
    return JSONResponse(
        status_code=200,
        content={
            "manager": type(manager).__name__,
            "repository": type(manager.repository).__name__,
        }
    )


@router.post("/start", response_model=Response)
def start():
    session = manager.create_session(client=None)

    return Response(
        session_id=str(session.session_id),
        message=read_markdown(os.path.join(ASSETS_PATH, "welcome_message.md"))
    )


@router.post("/message")
def message(req: Response):
    try:
        session = manager.get_session(req.session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")

    response = f"Echo: {req.message}"

    session.add_chat_iteration(
        ChatMessage(

        )
    )

    return {"response": response}