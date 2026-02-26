from pydantic import BaseModel
import datetime

class WeatherPostSchema(BaseModel):
    temperature: float
    relative_humidity: float
    wind_speed: float
    precipitation: float
    time: datetime.datetime
    city_id: int

class WeatherGetSchema(WeatherPostSchema):
    id: int
