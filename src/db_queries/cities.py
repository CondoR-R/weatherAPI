from sqlalchemy import select

from src.schemas.cities import CitiesDbPostSchema, CitiesGetSchema
from src.database import session
from src.models import CitiesModel

async def insert_city(city: CitiesDbPostSchema):
    '''
    Добавляет город в таблицу cities, для которых отслеживается прогноз.
    Принимает параметр city типа CitiesDbPostSchema, который включает в себя:
    - city: название города
    - user_id: id пользователя который добавляет город
    - lat: широта
    - lon: долгота
    - timezone: часовой пояс координат в формате секунд
    Возвращает id добавленного города
    '''
    async with session() as conn:
        # проверка на новый город для пользователя
        query = (
            select(CitiesModel)
            .where(CitiesModel.city==city.city)
            .where(CitiesModel.user_id==city.user_id)
        )
        result = await conn.execute(query)
        if result.scalars().first():
            raise ValueError()

        new_city = CitiesModel(
            city=city.city,
            user_id=city.user_id,
            lat=city.lat,
            lon=city.lon,
            timezone=city.timezone
        )
        conn.add(new_city)
        await conn.flush() 
        await conn.commit()
        return new_city.id


# работа с id пользователя
async def select_cities(user_id: int):
    '''
    Возвращает список городов для текущего пользователя 
    из таблицы cities, для которых доступен прогноз погоды.
    '''
    async with session() as conn:
        query = select(CitiesModel).where(CitiesModel.user_id==user_id)
        result = await conn.execute(query)
        result_orm = result.scalars().all()
        cities = [CitiesGetSchema.model_validate(row, from_attributes=True).city for row in result_orm]
        return cities


async def select_coords():
    '''
    Возращает все координаты (города), содержащиеся в таблице cities
    '''
    async with session() as conn:
        query = select(CitiesModel)
        result = await conn.execute(query)
        result_orm = result.scalars().all()
        coords = [CitiesGetSchema.model_validate(row, from_attributes=True) for row in result_orm]
        return coords


async def select_city(city: str, user_id: str):
    '''
    Возвращает запись в таблице cities, удовлетворяющую параметрам запроса
    Принимаемые параметры:
    - city: название города
    - user_id: id пользователя
    '''
    async with session() as conn:
        query = (
            select(CitiesModel)
            .where(CitiesModel.city==city)
            .where(CitiesModel.user_id==user_id)
        )
        result = await conn.execute(query)
        return result.scalars().first()
