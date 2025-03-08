from pydantic import BaseModel, Field, ConfigDict, AfterValidator, IPvAnyAddress, ValidationError
from typing_extensions import Annotated

from api_v1.controller_management.checkers.checkers_core import HostData
from api_v1.controller_management.schemas import AllowedControllers, get_value_as_string


class Base(BaseModel):
    model_config = ConfigDict()


class TypeController(Base):
    type_controller: AllowedControllers
    ip_address: IPvAnyAddress


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


if __name__ == '__main__':
    x = TypeController(type_controller='Swarco')
    print(x)
