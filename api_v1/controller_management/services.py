import ipaddress
import json

from pydantic import ValidationError

from .schemas import (
    Ipv4,
AllowedControllers,
AllowedTypeRequestGetState,
GetStateByIpv4
)

class DataHosts:
    """
    Класс валидации данных.
    """

    def __init__(self, income_data: dict):
        print(f'income_data: {income_data}')
        self.income_data = income_data
        self.good_hosts = {}
        self.bad_hosts = {}

    def __repr__(self):
        return (f'self.income_data:\n{json.dumps(self.income_data, indent=4)}\n'
                f'self.good_hosts: {json.dumps(self.good_hosts, indent=4)}\n'
                f'self.bad_hosts: {json.dumps(self.bad_hosts, indent=4)}')

    def validate_income_data(self):
        for ip, data_host in self.income_data.items():
            is_valid, e_msg = False, None
            try:
                # print(f'ip: {ip}\ndata_host: {data_host}')
                ipaddress.IPv4Address(ip)
                GetStateByIpv4(**data_host)
                is_valid = True
            except ipaddress.AddressValueError:
                e_msg = 'invalid ip address'
            except ValidationError:
                e_msg = 'invalid host data'
            if is_valid:
                self.good_hosts |= {ip: data_host}
            else:
                data_host['error'] = e_msg
                self.bad_hosts |= {ip: data_host}

    def json_to_dict(self):
        pass