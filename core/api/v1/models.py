from pydantic import BaseModel


class Response(BaseModel):
    session_id: str
    message: str
