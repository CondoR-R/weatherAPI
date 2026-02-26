from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import httpx

from src.api.depends import CoordsDep
from src.open_meteo_queries import get_current_weather as get_current
from src.schemas.current_weather import CurrentWeatherResponseSchema

router = APIRouter()

@router.get('/current_weather', response_model=CurrentWeatherResponseSchema, tags=['weather'], summary='Get current weather')
async def get_current_weather(coords: CoordsDep):
    '''
    Возращает текущую погоду для введенных координат
    Принимает параметры:
    - **lat**: широта (от -90 до 90)
    - **lon**: долгота (от -180 до 180)
    '''
    try:
        result = await get_current(coords)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code, 
            detail=f'An error on the part of the Open Meteo API: {exc.response.text}'
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504, 
            detail='Open Meteo API did not respond in time'
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Something went wrong'
        )
        
    return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder(result)
        )
