# файл вспомогательных функций
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status

from src.schemas.weather import WeatherPostSchema
from src.db_queries.users import select_user_by_id

def hourly_weather_formation(response, city_id: int) -> list[WeatherPostSchema]:
    '''
    Приводит почасовой прогноз погоды для города в необходимый для добавления в
    базу данных формат.
    Принимаемые параметры:
    - response: экземпляр списка ответа Open Meteo API
    - city_id: id города из таблицы cities
    Возращает список прогнозов погоды
    '''
    hourly = response.Hourly()

    start_utc = datetime.fromtimestamp(hourly.Time(), tz=timezone.utc)
    interval = timedelta(seconds=hourly.Interval())
    utc_offset = timedelta(seconds=response.UtcOffsetSeconds())
    tz = timezone(utc_offset)
    time_list = [
        ((start_utc + i * interval) + utc_offset).astimezone(tz)
        for i in range(hourly.Variables(0).ValuesLength())
    ]

    hourly_temperature = hourly.Variables(0).ValuesAsNumpy()
    hourly_relative_humidity = hourly.Variables(1).ValuesAsNumpy()
    hourly_precipitation = hourly.Variables(2).ValuesAsNumpy()
    hourly_wind_speed = hourly.Variables(3).ValuesAsNumpy()

    weather_list = []
    for j in range(len(time_list)):
        weather = WeatherPostSchema(
            city_id=city_id,
            temperature=hourly_temperature[j],
            relative_humidity=hourly_relative_humidity[j],
            wind_speed=hourly_wind_speed[j],
            precipitation=hourly_precipitation[j],
            time=time_list[j]
        )
        weather_list.append(weather)
    return weather_list


def set_time(hours: int, gtm: int) -> datetime:
    '''
    Преобразует время к нулевому часовому поясу
    Принимаемые параметры:
    - hours: час текущего дня в выбранном часовом поясе
    - gtm: часовой пояс в секундах
    Возвращает время по нулевому часовому поясу
    '''
    time = datetime.now()
    year = time.year
    month = time.month
    day = time.day
    minute = 0
    seconds = 0
    query_time = datetime(year, month, day, hours, minute, seconds) + timedelta(seconds=gtm)
    return query_time


async def check_user(id: int):
    '''
    Проверяет есть ли пользователь с таким id в базе данных, если нет, то 
    пробрасывает ошибку.
    '''
    user_from_db = await select_user_by_id(id)
    if not user_from_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'User with ID {id} not found'
        )

