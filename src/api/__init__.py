from fastapi import APIRouter

from src.api.current_weather import router as current_weather_router
from src.api.cities import router as cities_router
from src.api.hourly_weather import router as hourly_router
from src.api.users import router as users_router

router = APIRouter()
router.include_router(current_weather_router)
router.include_router(cities_router)
router.include_router(hourly_router)
router.include_router(users_router)

