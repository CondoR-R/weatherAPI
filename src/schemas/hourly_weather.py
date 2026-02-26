from pydantic import Field, BaseModel
from enum import Enum

from src.constants import len_100

class ParamsEnum(str, Enum):
    temperature = 'temperature'
    relative_humidity = 'relative_humidity'
    wind_speed = 'wind_speed'
    precipitation = 'precipitation'

class HourlyWeatherSchema(BaseModel):
    user_id: int
    city: str = Field(max_length=len_100)
    time: int = Field(ge=0, le=23)
    params: str = Field(','.join([param.value for param in ParamsEnum]))


