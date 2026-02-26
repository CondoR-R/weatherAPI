from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from typing import Annotated

primary_key = Annotated[int, mapped_column(primary_key=True)]

engine = create_async_engine('sqlite+aiosqlite:///./weather.db', echo=False)

session = async_sessionmaker(engine, expire_on_commit=False )

class Base(DeclarativeBase): 
    pass

async def create_tables():
    '''
    Создает таблицы базы данных при их отсутсвии
    '''
    async with engine.connect() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.commit()
