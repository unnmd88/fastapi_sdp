import pytest

from api_v1.controller_management import sorters, schemas


def test_instance_HostSorterSearchInDB():
    model = schemas.BaseFieldsSearchInDb(hosts=['3230', '11', '10.45.154.16'])
    obj = services.HostProcessorAfterSearchInDB(model)
    expected = {
        '3230': {
            schemas.AllowedDataHostFields.entity: schemas.AllowedMonitoringEntity.GET_FROM_DB
        },
        '11': {
            schemas.AllowedDataHostFields.entity: schemas.AllowedMonitoringEntity.GET_FROM_DB
        },
        '10.45.154.16': {
            schemas.AllowedDataHostFields.entity: schemas.AllowedMonitoringEntity.GET_FROM_DB
        }
    }
    assert obj._stack_hosts == expected

def test_get_hosts_data_for_search_db_HostSorterSearchInDB():

    hosts = ['3230', '11', '10.45.154.16', 'abra', 'cadabra']

    m = schemas.BaseFieldsSearchInDb(hosts=hosts)
    obj = services.HostProcessorAfterSearchInDB(m)

    hosts_as_model = [
        schemas.SearchHostsInDb(ip_or_name_from_user=ip_or_name_from_user) for ip_or_name_from_user in hosts
    ]
    assert obj.get_hosts_data_for_search_in_db() == hosts_as_model

def test_get_model_HostSorterSearchInDB():
    model = schemas.BaseFieldsSearchInDb(hosts=['3230', '11', '10.45.154.16'])
    obj = services.HostProcessorAfterSearchInDB(model)
    assert obj.model_for_search_in_db == obj._get_model_for_search_in_db()

def test_get_hosts_and_bad_hosts_as_dict_HostSorterSearchInDB():

    fake_model = schemas.BaseFieldsSearchInDb(hosts=['3230', '11', '10.45.154.16'])
    obj = services.HostProcessorAfterSearchInDB(fake_model)

    bad_hosts = [
        {'string': {'entity': 'get_host_property', 'errors': ['not found in database']}},
        {'abra': {'entity': 'get_host_property', 'errors': ['not found in database']}},
        {'cadabra': {'entity': 'get_host_property', 'errors': ['not found in database']}}
    ]
    bad_hosts_dict = {
        'string': {'entity': 'get_host_property', 'errors': ['not found in database']},
        'abra': {'entity': 'get_host_property', 'errors': ['not found in database']},
        'cadabra': {'entity': 'get_host_property', 'errors': ['not found in database']}
    }

    hosts = {
        '10.179.28.9': {'number': '11', 'type_controller': 'Swarco',
                         'address': 'Бережковская наб. д.22, 24    ЗАО (ЗАО-9)', 'description': 'Приоритет ОТ'},
         '10.179.56.1': {'number': '12', 'type_controller': 'Поток (P)',
                         'address': 'Щербаковская ул. - Вельяминовская ул. д.6к1,32   ВАО (ВАО-4)',
                         'description': 'Приоритет ОТ'},
         '10.179.40.9': {'number': '13', 'type_controller': 'Swarco',
                         'address': 'Шереметьевская ул. д.60,62,29,27к1 - Марьиной Рощи 11-й пр-д (СВАО-2)',
                         'description': None}
    }

    obj.hosts_with_errors, obj.hosts = bad_hosts, hosts
    assert obj.get_bad_hosts_as_dict() == bad_hosts_dict
    assert obj.get_good_hosts_and_bad_hosts_as_dict() == (hosts | bad_hosts_dict)


if __name__ == '__main__':

    pytest.main()