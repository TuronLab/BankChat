from fastapi import FastAPI

from config import CHAT_LOGGER


def create_bank_chat_app():
    from api.v1.router import router
    CHAT_LOGGER.info('STARTING BANK CHAT SERVICE')
    app = FastAPI()
    app.include_router(router, tags=['Bank Chat'])
    return app