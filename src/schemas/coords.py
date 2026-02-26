from pydantic import BaseModel, Field

class CoordsSchema(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
