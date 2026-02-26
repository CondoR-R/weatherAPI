from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base, primary_key
from src.constants import len_100

class UsersModel(Base):
    __tablename__ = 'users'

    id: Mapped[primary_key]
    user_name: Mapped[str] = mapped_column(String(len_100), unique=True)

    
