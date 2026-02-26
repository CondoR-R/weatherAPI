from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from src.api.depends import CityWeatherQueryDep
from src.db_queries.cities import select_city
from src.db_queries.weather import select_weather
from src.functions import set_time, check_user
from src.schemas.hourly_weather import ParamsEnum

router = APIRouter()

@router.get('/weather', tags=['weather'], summary='Get hourly weather')
async def get_weather(query: CityWeatherQueryDep):
    '''
    Возвращает прогноз погоды на текущий день для введенного города 
    в выбранное время.
    Принимает параметры:
    - **user_id**: id текущего пользователя
    - **city**: название города
    - **time*: час, для которого необходимо вернуть прогноз погоды (от 0 до 23)
    - **params**: возращаемые параметры погоды, при отсутсвии данного параметра 
    вернет все возможные параметры погоды. Параметры погоды записываются через
    запятую без пробела. Возможные параметры:
        - **temperature**: температура
        - **relative_humidity**: относительная влажность
        - **wind_speed**: скорость ветра
        - **precipitation**: осадки
    '''
    try:
        await check_user(query.user_id)
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Internal server error'
        )

    if len(query.params.split(' ')) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Parameters must be written without spaces.'
        )
    
    params = query.params.split(',')
    for param in params:
        if param not in [param.value for param in ParamsEnum]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'The query parameter {param} is not a valid parameter from the list of available parameters. Available parameters for the request: {', '.join([param.value for param in ParamsEnum])}.'
            )
    
    try:
        city = await select_city(query.city, query.user_id)
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Internal server error'
        )
    
    if not city:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'City {query.city} was not found in the database for user with ID {query.user_id}'
        )
    
    time = set_time(query.time, city.timezone)
    
    try:
        weather = await select_weather(city.id, time)
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Internal server error'
        )

    weather_dict = weather.model_dump()
    if not weather_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Weather for {query.city} for {time} was not found in the database.'
        )
    
    result = {k: weather_dict[k] for k in params if k in weather_dict}

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=result
    )

