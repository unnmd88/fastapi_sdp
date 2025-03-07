from collections.abc import KeysView
from pysnmp.hlapi.v3arch.asyncio import *
from sdp_lib.management_controllers.snmp.oids import Oids


snmp_engine = SnmpEngine()


async def snmp_get(
        ipv4: str,
        community: str,
        oids: list[str | Oids] | KeysView[str | Oids],
        engine: SnmpEngine = SnmpEngine(),
        timeout: float = 0.2,
        retries: int = 0
):
    error_indication, error_status, error_index, var_binds = await get_cmd(
        engine,
        CommunityData(community),
        await UdpTransportTarget.create((ipv4, 161), timeout=timeout, retries=retries),
        ContextData(),
        *[ObjectType(ObjectIdentity(oid)) for oid in oids]
    )
    return error_indication, var_binds

async def snmp_get_next(
        ipv4: str,
        community: str,
        oids: list[str | Oids] | KeysView[str | Oids],
        engine: SnmpEngine = SnmpEngine(),
        timeout: float = 0.2,
        retries: int = 0
):
    error_indication, error_status, error_index, var_binds = await next_cmd(
        engine,
        CommunityData(community),
        await UdpTransportTarget.create((ipv4, 161), timeout=timeout, retries=retries),
        ContextData(),
        *[ObjectType(ObjectIdentity(oid)) for oid in oids]
    )
    return error_indication, var_binds