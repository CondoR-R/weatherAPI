from pydantic import BaseModel, Field

from src.constants import len_100

class UsersPostSchema(BaseModel):
    user_name: str = Field(max_length=len_100)

class UsersResponseSchema(BaseModel):
    id: int
