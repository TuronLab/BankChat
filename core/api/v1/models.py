from pydantic import BaseModel


class ResponseStartSession(BaseModel):
    session_id: str
    message: str

class UserPetitionChat(BaseModel):
    session_id: str
    message: str

class ResponseChat(BaseModel):
    session_id: str
    message: str
