import pytest

from api_v1.controller_management import services, schemas


def test_instance_HostSorterSearchInDB():
    model = schemas.GetHostsStaticDataFromDb(hosts=['3230', '11', '10.45.154.16'])
    obj = services.HostSorterSearchInDB(model)
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

def test_get_model_HostSorterSearchInDB():
    model = schemas.GetHostsStaticDataFromDb(hosts=['3230', '11', '10.45.154.16'])
    obj = services.HostSorterSearchInDB(model)
    assert obj.model_for_search_in_db == obj._get_model_for_search_in_db()



if __name__ == '__main__':

    pytest.main()