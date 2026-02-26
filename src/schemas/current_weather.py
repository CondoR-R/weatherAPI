from pydantic import BaseModel

class CurrentWeatherResponseSchema(BaseModel):
    current_temperature: float
    current_wind_speed: float
    atmospheric_pressure: float

