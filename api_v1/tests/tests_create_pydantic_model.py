import pytest
from faker import Faker
from pydantic import ValidationError

from api_v1.controller_management.schemas import HostPropertiesBase, TrafficLightsObjectsTableFields
from sdp_lib.utils_common import get_random_word




faker = Faker()

def test_create_model_with_search_in_db_field__ipv4():
    for ip in [faker.ipv4() for _ in range(100)]:
        obj = HostPropertiesBase(ip_or_name_from_user=ip)
        assert obj.search_in_db_field == TrafficLightsObjectsTableFields.IP_ADDRESS

def test_create_model_with_search_in_db_field__number():
    for ip in [get_random_word() for _ in range(100)]:
        obj = HostPropertiesBase(ip_or_name_from_user=ip)
        assert obj.search_in_db_field == TrafficLightsObjectsTableFields.NUMBER



if __name__ == '__main__':

    pytest.main()