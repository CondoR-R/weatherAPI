from fastapi import APIRouter, status, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
import httpx

from src.db_queries.cities import insert_city, select_cities
from src.db_queries.weather import insert_weather
from src.open_meteo_queries import get_new_city_hourly_weather
from src.schemas.cities import CitiesDbPostSchema, CitiesPostSchema
from src.functions import hourly_weather_formation, check_user

router = APIRouter()

@router.post('/cities', response_model=str, tags=['cities'], summary='Add new city')
async def post_city(city: CitiesPostSchema):
    '''
    Добавляет новый город, для которого отслеживается прогноз погоды. 
    Делает запрос к Open Meteo API, чтобы сразу получить почасовой прогноз.
    Принимаемые параметры в теле запроса:
    - **city**: название города
    - **user_id**: id пользователя который добавляет город
    - **lat**: широта (от -90 до 90, значение по умолчанию - 0)
    - **lon**: долгота (от -180 до 180, значение по умолчанию - 0)
    '''
    try:
        await check_user(city.user_id)
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Internal server error'
        )

    try:
        response, timezone = await get_new_city_hourly_weather(city)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code, 
            detail=f'City ​​added successfully! However, an error occurred with the Open Meteo API when attempting to retrieve the hourly forecast for the city: {exc.response.text}'
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504, 
            detail='The city has been successfully added! However, when attempting to retrieve the hourly weather forecast for the city, the Open Meteo API timed out.'
        )
        
    new_city = CitiesDbPostSchema(
        city=city.city,
        user_id=city.user_id,
        lat=city.lat,
        lon=city.lon,
        timezone=timezone
    )

    try:
        id = await insert_city(new_city)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='City already exists for this user'
        )
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Internal server error'
        )

    weather = hourly_weather_formation(response, id)

    try:
        await insert_weather(weather)
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Internal server error'
        )
        
    return JSONResponse(
        status_code=status.HTTP_201_CREATED, 
        content={'detail': 'City ​​added successfully'}
    )

    
@router.get('/cities', response_model=list[str], tags=['cities'], summary='Get cities')
async def get_cities(user_id: int):
    '''
    Принимает id пользователя для которого необходимо вывести список городов.
    Возвращает список городов, для которых отслеживается прогноз погоды
    '''
    try:
        await check_user(user_id)
        cities = await select_cities(user_id)
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Internal server error'
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Something went wrong'
        )
    
    return JSONResponse(status_code=status.HTTP_200_OK, content=cities)
