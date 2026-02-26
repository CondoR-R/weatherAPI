from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
import datetime

from src.database import Base, primary_key

class WeatherModel(Base):
    __tablename__ = 'weather'

    id: Mapped[primary_key]
    temperature: Mapped[float]
    relative_humidity: Mapped[float] 
    wind_speed: Mapped[float]
    precipitation: Mapped[float]
    time: Mapped[datetime.datetime]
    city_id: Mapped[int] = mapped_column(ForeignKey('cities.id', ondelete='CASCADE'))
    

    
