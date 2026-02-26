import asyncio

from src.db_queries.cities import select_coords
from src.db_queries.weather import update_weather
from src.open_meteo_queries import get_hourly_weather

async def update_hourly_weather():
    '''
    Обновляет данные о прогнозе погоды для известных городов
    '''
    coords = await select_coords()
    if len(coords) == 0: 
        return
    params = {
        'latitude': [coord.lat for coord in coords],
        'longitude': [coord.lon for coord in coords],
        'hourly': ['temperature_2m', 'relative_humidity_2m', 'precipitation', 'wind_speed_10m'],
        'timezone': 'auto',
        'forecast_days': 1,
    }
    weather_list = await get_hourly_weather(coords, params)
    await update_weather(weather_list)


async def background_task():
    '''
    Запускает процедуру обновления прогноза погоды раз в 15 минут
    '''
    while True:
        print('Запрос к Open Meteo API')
        await update_hourly_weather()
        await asyncio.sleep(15 * 60)
