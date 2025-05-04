from api_v1.controller_management.schemas import TrafficLightsObjectsTableFields
from sdp_lib.utils_common.utils_common import check_is_ipv4


def get_field_for_search_in_db(name_or_ipv4: str) -> str:

    if check_is_ipv4(name_or_ipv4):
        return str(TrafficLightsObjectsTableFields.IP_ADDRESS)
    return str(TrafficLightsObjectsTableFields.NUMBER)