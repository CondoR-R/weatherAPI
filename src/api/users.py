from fastapi import APIRouter, status, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from src.schemas.users import UsersResponseSchema, UsersPostSchema
from src.db_queries.users import select_user, insert_user

router = APIRouter()

@router.post('/users', response_model=UsersResponseSchema, tags=['users'], summary='Register or authorize a user')
async def post_users(user: UsersPostSchema):
    '''
    Принимает тело запроса с user_name - имя пользователя, если пользователь с таким именем 
    есть в базе, возвращает его id, если пользователя с таким именем нет - 
    создает его в базе и возвращает его id.
    '''
    # проверка на пустую строку/строку из одних пробелов
    if len(user.user_name.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail='The user_name field must not be empty.'
        )
    
    try:
        user_from_db = await select_user(user)
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Internal server error'
        )

    if user_from_db:
        return JSONResponse(
            status_code=status.HTTP_200_OK, 
            content={'id': user_from_db.id}
        )

    try:
        id = await insert_user(user)
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Internal server error'
        )

    return JSONResponse(
            status_code=status.HTTP_201_CREATED, 
            content={'id': id}
        )
    
