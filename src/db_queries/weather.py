from sqlalchemy import delete, select
import datetime

from src.schemas.weather import WeatherPostSchema, WeatherGetSchema
from src.database import session
from src.models.weather import WeatherModel

def create_new_weather(w: WeatherPostSchema):
    '''
    Вспомогательная функция, создающая экземпляр таблицы weather.
    Принимает параметр w: погода, которую необходимо 
    преобрзовать в экземпляр для таблицы weather.
    Возвращает объект типа WeatherModel.
    '''
    new_weather = WeatherModel(
                temperature=w.temperature,
                relative_humidity=w.relative_humidity,
                wind_speed=w.wind_speed,
                precipitation=w.precipitation,
                time=w.time,
                city_id=w.city_id
            )
    return new_weather


async def insert_weather(weather: list[WeatherPostSchema]):
    '''
    Добавляет список почасового прогноза для города.
    Принимает параметр weather - список почасового прогноза на сутки для города.
    '''
    async with session() as conn:
        for w in weather:
            new_weather = create_new_weather(w)
            conn.add(new_weather)
        await conn.commit()


async def update_weather(weather: list[WeatherPostSchema]):
    '''
    Обновляет записи о прогнозе погоды в таблице weather
    '''
    async with session() as conn:
        await conn.execute(delete(WeatherModel))
        for w in weather:
            new_weather = create_new_weather(w)
            conn.add(new_weather)
        await conn.commit()


async def select_weather(city_id: int, time: datetime.datetime):
    '''
    Возвращает прогноз погоды для города по времени
    Принимаемые параметры:
    city_id: id города, для которого необходим прогноз
    time: время, для которого необходим прогноз
    '''
    async with session() as conn:
        query = (
            select(WeatherModel)
            .where(WeatherModel.city_id==city_id)
            .where(WeatherModel.time==time)
        )
        result = await conn.execute(query)
        result_orm = result.scalars().first()
        return WeatherGetSchema.model_validate(result_orm, from_attributes=True)
