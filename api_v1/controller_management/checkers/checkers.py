from pydantic import BaseModel, IPvAnyAddress, field_validator
from pydantic_core import ValidationError, PydanticCustomError

from api_v1.controller_management.schemas import AllowedControllers, SearchinDbHostBodyForMonitoringAndManagementProxy, \
    TrafficLightsObjectsTableFields
from api_v1.controller_management.checkers.archive.custom_checkers import HostData


class TypeController(BaseModel):
    type_controller: AllowedControllers
    ip_adress: IPvAnyAddress


class FoundInDatabase(BaseModel):

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
                print(f'self.properties.model_dump(): {self.properties.model_dump()}')
                validate_class(**self.properties.model_dump())
            except ValidationError as e:
                self.properties.errors.append(e.errors(include_input=False))
                res = False
        return res

    def get_validate_classes(self):
        return (TypeController, )

    def get_validate_methods(self):
        """
        Возвращает список с методами валидаций.
        :return:
        """
        return [self.validate_all]


class AfterSearchInDbChecker(HostData):

    def __init__(self, ip_or_name: str, properties: SearchinDbHostBodyForMonitoringAndManagementProxy):
        super().__init__(ip_or_name, properties)
        self.properties: SearchinDbHostBodyForMonitoringAndManagementProxy = properties

    def validate_all(self):
        """
        Проверяет валидность найденной записи хоста из бд.
        Осуществляет проверку валидности хоста для запроса
        мониторинга или управления.
        :return: True, если проверка
                 использовать для мониторинга или управления.
        """
        if not self.validate_record():
            return False
        return True

    def validate_record(self):
        try:
            FoundInDatabase(db_records=self.properties.db_records)
            return True
        except ValidationError as e:
            self.properties.errors += e.errors(include_url=False, include_input=False)
            return False

    def get_validate_classes(self):
        return (FoundInDatabase, )

    def get_validate_methods(self):
        """
        Возвращает список с методами валидаций.
        :return:
        """
        return [self.validate_all]


if __name__ == '__main__':
    a = [1,2 ,3]
    try:
        FoundInDatabase(db_records=a)
    except ValidationError  as e:
        print(e.errors())
        print(e)
        # print(e)

