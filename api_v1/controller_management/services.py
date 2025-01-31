
from .schemas import (
    Ipv4,
AllowedControllers,
AllowedTypeRequestGetState,
GetStateByIpv4
)

class Validators:
    """
    Класс валидации данных.
    """

    def __init__(self, income_data: str | bytes):
        self.income_data = income_data

    def validate_income_data(self):
        pass

    def json_to_dict(self):
        pass