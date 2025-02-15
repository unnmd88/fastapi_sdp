import pytest
from faker import Faker
from pydantic import ValidationError

from api_v1.controller_management.schemas import TrafficLightsObjectsTableFields
from sdp_lib.utils_common import get_random_word


faker = Faker()


if __name__ == '__main__':

    pytest.main()