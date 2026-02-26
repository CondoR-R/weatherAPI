from pydantic import Field

from src.schemas.coords import CoordsSchema
from src.constants import len_100

class CitiesPostSchema(CoordsSchema):
    city: str = Field(max_length=len_100)
    user_id: int

class CitiesDbPostSchema(CitiesPostSchema):
    timezone: int

class CitiesGetSchema(CitiesPostSchema):
    id: int
