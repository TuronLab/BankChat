import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from starlette.responses import JSONResponse

from config import ASSETS_PATH, OPENAI_KEY, PROJECT_PATH, CHAT_LOGGER
from core.agents.custom_exception import VoidMessageException
from core.agents.greeter_agent import GreeterAgent
from core.agents.specialist_agent import SpecialistAgent
from core.agents.tools.tools import get_client_financial_overview, get_expert_contact_details, \
    get_client_profile_summary, get_total_liquidity, get_account_balance
from core.data.load_data import JSONCustomerDataLoader
from core.inferencer import OpenAIInferencer
from core.orchestrator import Orchestrator
from core.session_manager.custom_exceptions import UnknownSessionIdException
from core.session_manager.session_manager import SessionManager
from core.session_manager.session_repository import NoStorageRepository
from core.utils import read_markdown
from core.api.v1.models import Response

router = APIRouter()

manager = SessionManager(NoStorageRepository())
inferencer_engine = OpenAIInferencer(model="gpt-4.1-mini", api_key=OPENAI_KEY)
database_loader=JSONCustomerDataLoader(Path(os.path.join(PROJECT_PATH, "database_example", "dataset_example.json")))
tools = [get_account_balance, get_total_liquidity, get_client_profile_summary, get_expert_contact_details, get_client_financial_overview]

orchestrator = Orchestrator(
    inferencer_engine=inferencer_engine,
    database_loader=database_loader,
    greeter_agent=GreeterAgent(database_loader=database_loader, inferencer=inferencer_engine),
    specialist_agent=SpecialistAgent(inferencer=inferencer_engine, tools=tools)
)

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
            "inferencer_engine": {"type": type(orchestrator.inferencer_engine).__name__, "model": orchestrator.inferencer_engine.model},
            "database_loader": type(orchestrator.database_loader).__name__,
            "greeter_agent": type(orchestrator.greeter_agent).__name__,
            "specialist_agent": type(orchestrator.specialist_agent).__name__

        }
    )


@router.post("/start", response_model=Response)
def start():
    CHAT_LOGGER.info("Creating session...")
    session = manager.create_session(client=None)
    CHAT_LOGGER.info(f"Session created with id `{session.session_id}`")

    return Response(
        session_id=str(session.session_id),
        message=read_markdown(os.path.join(ASSETS_PATH, "welcome_message.md"))
    )


@router.post("/message", response_model=Response)
def message(req: Response):
    if req.message is not None and not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be void")

    try:
        CHAT_LOGGER.info("Trying to identify the requested session...")
        session = manager.get_session(req.session_id)
        CHAT_LOGGER.info("Successful identification.")
    except UnknownSessionIdException as e:
        CHAT_LOGGER.error(str(e))
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        CHAT_LOGGER.exception(f"Unexpected error while retrieving session {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

    try:
        response = orchestrator(session=session, message=req.message)
    except VoidMessageException:
        raise HTTPException(status_code=400, detail="Message cannot be void")
    except Exception as e:
        CHAT_LOGGER.exception(f"Unexpected error while retrieving session {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

    return Response(
        session_id=session.session_id,
        message=response
    )