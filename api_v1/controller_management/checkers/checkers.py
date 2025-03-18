from pydantic import BaseModel, ConfigDict, IPvAnyAddress, field_validator
from pydantic_core import ValidationError, PydanticCustomError
from sqlalchemy.sql.annotation import Annotated

from api_v1.controller_management.schemas import AllowedControllers, SearchinDbHostBodyMonitoringAndManagement
from api_v1.controller_management.checkers.archive.custom_checkers import HostData
from core.user_exceptions.validate_exceptions import NotFoundInDB
from pydantic import Field




class Base(BaseModel):
    model_config = ConfigDict()




class TypeController(Base):
    type_controller: AllowedControllers
    ip_address: IPvAnyAddress

class FoundInDatabase(BaseModel):

    db_records: list

    @field_validator('db_records')
    def must_be_unique(cls, v):
        if not v:
            raise PydanticCustomError(
                'Не найден в базе данных',
                'Хост не найден в базе данных',
                # dict(wrong_value=v)
            )
        if len(v) > 1:
            raise PydanticCustomError(
                'not unique',
                f'Найдено более одного хоста в базе данных, должен быть в единственном экземпляре',
                {
                    'Количество найденных хостов': len(v)
                }
            # dict(wrong_value=v)

            )






class MonitoringHostDataChecker(HostData):


    def validate_all(self):
        res = True
        for validate_class in self.get_validate_classes():
            try:
                validate_class(**self._get_full_host_data_as_dict())
            except ValidationError as e:
                self.add_error_entity_for_current_host(e.errors())
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

    def __init__(self, ip_or_name: str, properties: SearchinDbHostBodyMonitoringAndManagement):
        super().__init__(ip_or_name, properties)
        self.properties: SearchinDbHostBodyMonitoringAndManagement = properties

    def validate_all(self):
        if not self.validate_record():
            return False
        self.properties = self.properties.model_dump() | self.properties.db_records[0]
        print(f'self.properties::: {self.properties}')

        res = True
        for validate_class in self.get_validate_classes():
            try:
                validate_class(**self._get_full_host_data_as_dict())
            except ValidationError as e:
                self.add_error_entity_for_current_host(e.errors())
                res = False
        return res

    def validate_record(self):
        try:
            FoundInDatabase(db_records=self.properties.db_records)
            return True
        except ValidationError as e:
            self.add_error_entity_for_current_host(e.errors())
            return False


    def get_validate_classes(self):
        return (TypeController, )

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

