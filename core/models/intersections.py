
from sqlalchemy import DateTime, func, Column
from sqlalchemy.orm import Mapped

# from .base import Base
from core.models.base import Base


class TrafficLightsObjects(Base):
    __tablename__ = "toolkit_trafficlightsobjects"

    number: Mapped[int]
    description: Mapped[str]
    type_controller: Mapped[str]
    group: Mapped[str]
    ip_adress: Mapped[str]
    address: Mapped[str]
    time_create = Column(DateTime, default=func.now())
    time_update = Column(DateTime, default=func.now(), onupdate=func.now())

    def __str__(self):
        return f'{self.number} {self.address} {self.type_controller}'


class ControllerManagementOptions(Base):

    __tablename__ = "toolkit_controllermanagementoptions"

    type_controller: Mapped[str]
    group: Mapped[int]
    commands: Mapped[str]
    max_stage: Mapped[int]
    options: Mapped[str]
    sources: Mapped[str]
    time_create = Column(DateTime, default=func.now())
    time_update = Column(DateTime, default=func.now(), onupdate=func.now())

    def __str__(self):
        return (
            f'\ntype_controller: {self.type_controller}\n'
            f'group: {self.group}\n'
            f'commands: {self.commands}\n'
            f'max_stage: {self.max_stage}\n'
            f'options: {self.options}\n'
            f'sources: {self.sources}'
        )


if __name__ == '__main__':
    print(f'T: {type(TrafficLightsObjects.type_controller)}')