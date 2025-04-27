from typing import Annotated

from pydantic import BaseModel, IPvAnyAddress, field_validator, model_validator, SkipValidation
from pydantic_core import ValidationError, PydanticCustomError

from api_v1.controller_management.schemas import (
    AllowedControllers,
    AllowedManagementEntity,
    TrafficLightsObjectsTableFields,
    SearchinDbFields, AllowedManagementSources,
)
from api_v1.controller_management.checkers.archive.custom_checkers import HostData


class BaseFields(BaseModel):
    type_controller: AllowedControllers
    ip_adress: IPvAnyAddress


matches_stages = {
    AllowedControllers.SWARCO: range(9),
    AllowedControllers.PEEK: range(33),
    AllowedControllers.POTOK_P: range(129),
    AllowedControllers.POTOK_S: range(129),
}


matches_sources = {
    AllowedControllers.SWARCO: {AllowedManagementSources.man}
}

def validate_num_stage(type_controller, stage):
    # stages_range = matches_stages.get(type_controller)
    if int(stage) in matches_stages.get(type_controller, range(-1, -1)):
        return True
    return False


def validate_source(type_controller, source):
    if source in matches_sources.get(type_controller, ()):
        return True
    return False


class SetCommandFields(BaseFields):
    command: AllowedManagementEntity
    value: str | int
    source: Annotated[AllowedManagementSources | None, SkipValidation]

    @model_validator(mode='after')
    def value_validator(self):
        try:
            int(self.value)
        except ValueError:
            raise PydanticCustomError(
                f'Некорректное значение',
                f'Некорректное значение < value >: {self.value}',
                # dict(wrong_value=v)
            )
        if not validate_num_stage(self.type_controller, self.value):
            raise PydanticCustomError(
                f'Некорректное значение фазы',
                f'Некорректное значение фазы для данного типа контроллера < value >: {self.value}',
            )

        if not validate_source(self.type_controller, self.source):
            raise PydanticCustomError(
                f'Некорректное значение источника < source >',
                f'Некорректное значение источника команды < source >: {self.source}',
            )


class FoundInDatabaseFields(BaseModel):

    db_records: list

    @field_validator('db_records', mode='after')
    def complex_validator(cls, records):
        if not records:
            raise PydanticCustomError(
                'Не найден в базе данных',
                'Хост не найден в базе данных',
                # dict(wrong_value=v)
            )
        if len(records) > 1:
            raise PydanticCustomError(
                'not unique',
                f'Найдено более одного хоста в базе данных, должен быть в единственном экземпляре',
                {
                    'Количество найденных хостов': len(records)
                }
            # dict(wrong_value=v)

            )
        if not (records[0][TrafficLightsObjectsTableFields.IP_ADDRESS]):
            raise PydanticCustomError(
                'not if field',
                f'Нет данных об ip адресе у хоста в базе',
                {
                    'Нет ip': f'У найденного хоста нет информации об ip: {records[0][TrafficLightsObjectsTableFields.IP_ADDRESS]}'
                }
            )


class MonitoringHostDataChecker(HostData):

    def validate_all(self):
        res = True
        for validate_class in self.get_validate_classes():
            try:
                validate_class(**self.properties.model_dump())
            except ValidationError as e:
                self.properties.errors.append(e.errors(include_input=False))
                res = False
        return res

    def get_validate_classes(self):
        return (BaseFields, )

    def get_validate_methods(self):
        """
        Возвращает список с методами валидаций.
        :return:
        """
        return [self.validate_all]


class ManagementHostDataChecker(HostData):

    def validate_all(self):
        res = True
        for validate_class in self.get_validate_classes():
            try:
                validate_class(**self.properties.model_dump())
            except ValidationError as e:
                self.properties.errors.append(e.errors(include_input=False))
                res = False
        return res

    def get_validate_classes(self):
        return (SetCommandFields,)

    def get_validate_methods(self):
        """
        Возвращает список с методами валидаций.
        :return:
        """
        return [self.validate_all]


class AfterSearchInDbChecker(HostData):

    def __init__(self, ip_or_name: str, properties: SearchinDbFields):
        super().__init__(ip_or_name, properties)
        self.properties = properties

    def validate_record(self):
        try:
            FoundInDatabaseFields(db_records=self.properties.db_records)
            return True
        except ValidationError as e:
            self.properties.errors += e.errors(include_url=False, include_input=False)
            return False

    def get_validate_classes(self):
        return (FoundInDatabaseFields,)

    def get_validate_methods(self):
        """
        Возвращает список с методами валидаций.
        :return:
        """
        return [self.validate_all]




if __name__ == '__main__':
    a = [1,2 ,3]
    try:
        FoundInDatabaseFields(db_records=a)
    except ValidationError  as e:
        print(e.errors())
        print(e)
        # print(e)

