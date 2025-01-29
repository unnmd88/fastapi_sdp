from datetime import datetime

from sqlalchemy import DateTime, func, Column
from sqlalchemy.orm import Mapped

from .base import Base


class TrafficLightsObjects(Base):
    __tablename__ = "toolkit_trafficlightsobjects"

    number = Mapped[int]
    description = Mapped[str]
    type_controller = Mapped[str]
    group = Mapped[str]
    ip_adress = Mapped[str]
    address = Mapped[str]
    time_create = Column(DateTime, default=func.now())
    time_update = Column(DateTime, default=func.now(), onupdate=func.now())

    def __str__(self):
        return f'{self.number} {self.address} {self.type_controller}'