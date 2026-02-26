from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base, primary_key
from src.constants import len_100

class CitiesModel(Base):
    __tablename__ = 'cities'

    id: Mapped[primary_key]
    city: Mapped[str] = mapped_column(String(len_100))
    lat: Mapped[float]
    lon: Mapped[float]
    timezone: Mapped[int]
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))

    
