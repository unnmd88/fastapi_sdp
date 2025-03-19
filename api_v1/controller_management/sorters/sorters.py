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
    TrafficLightsObjectsTableFields, SearchinDbHostBody, ResponseSearchinDb
)
from api_v1.controller_management.checkers.checkers import MonitoringHostDataChecker


class HostSorterMonitoring(_BaseHostsSorters):

    def _get_checker_class(self):
        """
        Возвращает класс для валидации данных полей, применяемый в методе self.sort.
        :return:
        """
        return MonitoringHostDataChecker
