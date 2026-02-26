from typing import Annotated
from fastapi import Depends

from src.schemas.coords import CoordsSchema
from src.schemas.hourly_weather import HourlyWeatherSchema

CoordsDep = Annotated[CoordsSchema, Depends(CoordsSchema)]
CityWeatherQueryDep = Annotated[HourlyWeatherSchema, Depends(HourlyWeatherSchema)]
