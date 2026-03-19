from pydantic import BaseModel


class MessageRequest(BaseModel):
    session_id: str
    message: str


class StartResponse(BaseModel):
    session_id: str