from fastapi import FastAPI

from config import CHAT_LOGGER


def create_bank_chat_app():
    from core.api.v1.router import router
    CHAT_LOGGER.info('STARTING BANK CHAT SERVICE')
    app = FastAPI()
    app.include_router(router, tags=['Bank Chat'])
    return app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "core.api.v1.app:create_bank_chat_app",
        factory=True,
        host="0.0.0.0",
        port=8000,
    )
