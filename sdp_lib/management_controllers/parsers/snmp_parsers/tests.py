import asyncio

from pysnmp.entity.engine import SnmpEngine

from sdp_lib.management_controllers.snmp.stcip import CurrentStatesSwarco


async def main():
    o = CurrentStatesSwarco('10.45.154.16')
    r = await o.get_basic_states_and_parse(SnmpEngine())
    return r

if __name__ == '__main__':

    r = asyncio.run(main())
    print(r)
