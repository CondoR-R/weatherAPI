import openmeteo_requests
from datetime import timedelta

from src.schemas.coords import CoordsSchema
from src.schemas.current_weather import CurrentWeatherResponseSchema
from src.schemas.cities import CitiesGetSchema, CitiesPostSchema
from src.schemas.weather import WeatherPostSchema
from src.functions import hourly_weather_formation

url = 'https://api.open-meteo.com/v1/forecast'

async def get_weather(params) -> list:
    '''
    Выполяет запрос к Open Meteo API.
    Принимает параметр params - словарь с необходимыми параметрами запроса.
    Возвращает ответ от API.
    '''
    openmeteo = openmeteo_requests.AsyncClient()
    responses = await openmeteo.weather_api(url, params=params)
    return responses


async def get_current_weather(coords: CoordsSchema) -> CurrentWeatherResponseSchema:
    '''
    Получает текущий прогноз погоды.
    Принимаемый параметр - coords: координаты локации (lat, lon).
    Возвращает полученную от API текущую погоду.
    '''
    params = {
        'latitude': coords.lat,
        'longitude': coords.lon,
        'current': ['temperature_2m', 'wind_speed_10m', 'pressure_msl'],
    }
    responses = await get_weather(params)
    response = responses[0]
    current = response.Current()

    weather = CurrentWeatherResponseSchema(
        current_temperature=current.Variables(0).Value(),
        current_wind_speed=current.Variables(1).Value(),
        atmospheric_pressure=current.Variables(2).Value(),
    )
    return weather


async def get_new_city_hourly_weather(city: CitiesPostSchema):
    '''
    Получает почасовой прогноз погоды для нового города.
    Принимает параметр city - город, для которого необходимо 
    получить прогноз погоды.
    Возвращает полученный ответ от API (response) и часовой пояс в секундах.
    '''
    params = {
        'latitude': city.lat,
        'longitude': city.lon,
        'hourly': ['temperature_2m', 'relative_humidity_2m', 'precipitation', 'wind_speed_10m'],
        'timezone': 'auto',
        'forecast_days': 1,
    }
    responses = await get_weather(params)
    response = responses[0]

    utc_offset = timedelta(seconds=response.UtcOffsetSeconds())
    tz = int(utc_offset.total_seconds())
    return response, tz


async def get_hourly_weather(cities: list[CitiesGetSchema], params) -> list[WeatherPostSchema]:
    '''
    Получает почасовой прогноз для списка городов.
    Принимаемые параметры:
    - cities: список городов
    - params: параметры запроса
    Возвращает список прогнозов погоды.
    '''
    responses = await get_weather(params)

    weather_list = []
    for i in range(len(responses)):
        response = responses[i]
        weather = hourly_weather_formation(response, cities[i].id)
        weather_list.extend(weather)
    return weather_list
