from sqlalchemy import select

from src.database import session
from src.models.users import UsersModel
from src.schemas.users import UsersPostSchema

async def insert_user(user: UsersPostSchema) -> int:
    async with session() as conn:
        new_user = UsersModel(user_name=user.user_name)
        conn.add(new_user)
        await conn.flush()
        await conn.commit()
        return new_user.id


async def select_user(user: UsersPostSchema) -> int:
    async with session() as conn:
        query = select(UsersModel).where(UsersModel.user_name==user.user_name)
        result = await conn.execute(query)
        return result.scalars().first()


async def select_user_by_id(id: int):
    async with session() as conn:
        query = select(UsersModel).where(UsersModel.id==id)
        result = await conn.execute(query)
        return result.scalars().first()
