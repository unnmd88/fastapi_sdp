import pprint
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurveSignatureAlgorithm

from api_v1.controller_management.sorters.sorters_core import (
    _BaseHostsSorters,
    _HostSorterMonitoringAndManagement
)
from api_v1.controller_management.schemas import (
    NumbersOrIpv4,
    SearchHostsInDb,
    AllowedDataHostFields,
    TrafficLightsObjectsTableFields
)
from api_v1.controller_management.checkers.checkers import HostData, MonitoringHostDataChecker
from core.user_exceptions.validate_exceptions import NotFoundInDB


class HostSorterSearchInDB(_BaseHostsSorters):
    """
    Класс сортировок хостов, преданных пользователем для последующего
    поиска в БД.
    """

    def __init__(self, income_data: NumbersOrIpv4):
        super().__init__(income_data)
        self._stack_hosts: set | None = None
        self.hosts_after_search: list | None = None

    def __repr__(self):
        return (
            f'self.income_data: {self.income_data}\n'
            f'self.hosts_after_search: {self.hosts_after_search}\n'
            f'self._stack_hosts: {self._stack_hosts}\n'
            f'self.good_hosts: {self.good_hosts}\n'
            f'self.hosts: {self.income_hosts}\n'
            f'self.bad_hosts: {self.bad_hosts}\n'
            # f'self.hosts_after_search_in_db: {self.hosts_after_search}\n'
        )

    def _get_income_hosts_as_set(self, income_hosts: list | dict) -> set[str]:
        """
        Преобразует income_hosts хостов в set.
        :param income_hosts: income_hosts от пользователя.
        :return: income_hosts в виде set.
        """
        if isinstance(income_hosts, list):
            return set(income_hosts)
        elif isinstance(income_hosts, dict):
            return set(income_hosts.keys())
        raise ValueError('Переданный тип должен быть list или dict')

    #Deprecated
    def get_hosts_data_for_search_in_db(self) -> list[SearchHostsInDb]:
        """
        Возвращает список с экземплярами модели, полученной в self._get_model_for_search_in_db(),
        для формирования stmt.
        :return: list с экземплярами модели, полученной self._get_model_for_search_in_db().
                 Пример:
                 [
                 SearchHostsInDb(ip_or_name_from_user='10.45.154.16', search_in_db_field='ip_adress'),
                 SearchHostsInDb(ip_or_name_from_user='11', search_in_db_field='number'),
                 SearchHostsInDb(ip_or_name_from_user='abracadabra', search_in_db_field='number'),
                 SearchHostsInDb(ip_or_name_from_user='413-P', search_in_db_field='number')
                 ]
        """
        return [SearchHostsInDb(ip_or_name_from_user=host) for host in self.income_hosts]

    def sorting_hosts_after_search_from_db(self) -> dict[str, dict[str, Any]]:
        """
        Сортирует хосты: если хост был найден в БД, отправляет в self.good_hosts, иначе в self.bad_hosts.
        Также приводит свойства хостов(dict) к общему виду, см. описание founded_in_db_hosts и self.bad_hosts.
        founded_in_db_hosts: dict, в который будут добавляться хосты, найденные в БД.
                             Пример:
                             {
                             "10.179.56.1": {
                             "number": "12",
                             "type_controller": "Поток (P)",
                             "address": "Щербаковская ул. - Вельяминовская ул. д.6к1,32   ВАО (ВАО-4)",
                             "description": "Приоритет ОТ"
                             },
                             "10.179.40.9": {
                             "number": "13",
                             "type_controller": "Swarco",
                             "address": "Шереметьевская ул. д.60,62,29,27к1 - Марьиной Рощи 11-й пр-д (СВАО-2)",
                             "description": null
                             }
                             }
        self.bad_hosts: В контексте данного метода это list с хостами, которые не были найдены в БД.
                        Пример:
                        [
                        {'string': {'errors': ['not found in database']}},
                        {'abra': {'errors': ['not found in database']}},
                        {'cadabra': {'errors': ['not found in database']}}
                        ]
        :return: Атрибут self.good_hosts с хостами, найденными в БД.
        """

        self.good_hosts = {}
        self._stack_hosts = self._get_income_hosts_as_set(self.income_hosts)
        for found_record in self.hosts_after_search:
            found_record = dict(found_record)
            self._remove_found_host_from_stack_hosts(found_record)
            self.good_hosts |= self._build_properties_for_good_host(found_record)
        self._process_hosts_not_found_in_db()
        return self.good_hosts

    def refactor_sorting_hosts_after_search_from_db(self) -> dict[str, dict[str, Any]]:
        """
        Сортирует хосты: если хост был найден в БД, отправляет в self.good_hosts, иначе в self.bad_hosts.
        Также приводит свойства хостов(dict) к общему виду, см. описание founded_in_db_hosts и self.bad_hosts.
        founded_in_db_hosts: dict, в который будут добавляться хосты, найденные в БД.
                             Пример:
                             {
                             "10.179.56.1": {
                             "number": "12",
                             "type_controller": "Поток (P)",
                             "address": "Щербаковская ул. - Вельяминовская ул. д.6к1,32   ВАО (ВАО-4)",
                             "description": "Приоритет ОТ"
                             },
                             "10.179.40.9": {
                             "number": "13",
                             "type_controller": "Swarco",
                             "address": "Шереметьевская ул. д.60,62,29,27к1 - Марьиной Рощи 11-й пр-д (СВАО-2)",
                             "description": null
                             }
                             }
        self.bad_hosts: В контексте данного метода это list с хостами, которые не были найдены в БД.
                        Пример:
                        [
                        {'string': {'errors': ['not found in database']}},
                        {'abra': {'errors': ['not found in database']}},
                        {'cadabra': {'errors': ['not found in database']}}
                        ]
        :return: Атрибут self.good_hosts с хостами, найденными в БД.
        """

        self.good_hosts = {}
        self._stack_hosts = self.income_data.model_dump()
        print(f'self.hosts_after_search:: {self.hosts_after_search}')
        for found_record in self.hosts_after_search:
            found_record = dict(found_record)
            self.add_record(found_record)
            # self._remove_found_host_from_stack_hosts(found_record)
            # self.good_hosts |= self._build_properties_for_good_host(found_record)
        print(f'self.income_data: {self.income_data}')
        print(f'self.income_hosts: {self.income_hosts}')
        for k, v in self.income_hosts.items():
            print(f'k: {k}\v: {v}')
        self._process_hosts_not_found_in_db()
        return self.good_hosts

    def add_record(self, found_record: dict[str, Any]):

        number, ip = found_record[TrafficLightsObjectsTableFields.NUMBER], found_record[TrafficLightsObjectsTableFields.IP_ADDRESS]
        if number and number in self.income_hosts:
            key = number
        elif found_record[TrafficLightsObjectsTableFields.IP_ADDRESS] in self.income_hosts:
            key = ip
        else:
            return
        self.income_hosts[key][AllowedDataHostFields.db_records].append(found_record)
        self.income_hosts[key][AllowedDataHostFields.count] += 1
        self.income_hosts[key][AllowedDataHostFields.found] = True



    def _process_hosts_not_found_in_db(self) -> None:
        """
        Обрабатывает хосты из self._stack_hosts, которые не были найдены в БД. Добавляет
        словарь с полем errors(list) и текстом ошибки методом self.add_host_to_container_with_bad_hosts.
        Пример:
            "abra": {
                "errors": ["Не найден в базе данных, ip: 'abra'"]
            }
        :return: None.
        """
        for current_name_or_ipv4 in self._stack_hosts:
            current_host = HostData(ip_or_name=current_name_or_ipv4, properties={})
            e = NotFoundInDB(field_name=str(AllowedDataHostFields.ip_or_name), input_val=current_name_or_ipv4)
            current_host.add_error_entity_for_current_host(e)
            self.add_host_to_container_with_bad_hosts(current_host.ip_or_name_and_properties_as_dict)

    def _remove_found_host_from_stack_hosts(self, found_host: dict[str, str]):
        """
        Удаляет найденный в БД хост из self._stack_hosts.
        :param found_host: Запись о хосте, найденная в БД.
                           Пример:
                           {
                           'number': '11', 'ip_adress': '10.179.28.9', 'type_controller': 'Swarco',
                           'address': 'Бережковская наб. д.22, 24    ЗАО (ЗАО-9)', 'description': 'Приоритет ОТ'
                           }

        :return: None.
        """

        if found_host[str(TrafficLightsObjectsTableFields.NUMBER)] in self._stack_hosts:
            self._stack_hosts.remove(found_host[str(TrafficLightsObjectsTableFields.NUMBER)])
        elif found_host[str(TrafficLightsObjectsTableFields.IP_ADDRESS)] in self._stack_hosts:
            self._stack_hosts.remove(found_host[str(TrafficLightsObjectsTableFields.IP_ADDRESS)])
        else:
            raise ValueError('DEBUG: Найденный хост в БД должен содержаться в self.hosts_for_response!!')

    def _build_properties_for_good_host(self, record_from_db) -> dict[str, str]:
        """
        Формирует свойства хоста в виде словаря.
        :param record_from_db: Запись, найденная в БД.
                               Пример:
                              {
                               'number': '11', 'ip_adress': '10.179.28.9', 'type_controller': 'Swarco',
                               'address': 'Бережковская наб. д.22, 24    ЗАО (ЗАО-9)', 'description': 'Приоритет ОТ'
                               }
        :return: dict со свойствами хоста общего вида, где ключом является ip адрес, а значением остальные
                 свойства dict record_from_db
                 Пример:
                 "10.179.28.9":
                 {
                    "number": "11",
                    "type_controller": "Swarco",
                    "address": "Бережковская наб. д.22, 24    ЗАО (ЗАО-9)",
                    "description": "Приоритет ОТ"
                 }
        """
        ipv4 = record_from_db.pop(str(TrafficLightsObjectsTableFields.IP_ADDRESS))
        return {ipv4: record_from_db}


class HostSorterMonitoring(_HostSorterMonitoringAndManagement):

    def _get_checker_class(self):
        """
        Возвращает класс для валидации данных полей, применяемый в методе self.sort.
        :return:
        """
        return MonitoringHostDataChecker