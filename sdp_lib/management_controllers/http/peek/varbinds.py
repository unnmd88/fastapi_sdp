import os
import pprint
from enum import IntEnum, StrEnum
from functools import cached_property



"""
ALL_MPP_INPUTS=MPP_MAN MPP_FL MPP_OFF MPP_PH1 MPP_PH2 MPP_PH3 MPP_PH4 MPP_PH5 MPP_PH6 MPP_PH7 MPP_PH8
MPP_STAGES_INPUTS=MPP_PH1 MPP_PH2 MPP_PH3 MPP_PH4 MPP_PH5 MPP_PH6 MPP_PH7 MPP_PH8
START_NAME_MAN=MPP_
PREFIX_MAN_STAGE_PEEK=MPP_PH
MPP_MANUAL=MPP_MAN
MPP_FLASH=MPP_FL
MPP_DARK=MPP_OFF
"""



all_mpp_inputs = set(os.getenv('ALL_MPP_INPUTS').split())
mpp_stages_inputs = set(os.getenv('MPP_STAGES_INPUTS').split())
MPP_MAN = os.getenv('MPP_MANUAL')
PREFIX_MAN_STAGE_PEEK = os.getenv('PREFIX_MAN_STAGE_PEEK')
START_NAME_MAN = os.getenv('START_NAME_MAN')

key_payload = 'par_name'
val_payload = 'par_value'
inputs_prefix = os.getenv('INPUT_PREFIX_FOR_SET_VAL')

class ActuatorAsChar(StrEnum):
    VF     = '-'
    OFF    = 'ВЫКЛ'
    ON     = 'ВКЛ'


class ActuatorAsValue(StrEnum):
    VF     = '0'
    OFF    = '1'
    ON     = '2'

class InputsStructure(IntEnum):

    INDEX     = 0
    NUM       = 1
    NAME      = 2
    STATE     = 3
    TIME      = 4
    ACTUATOR  = 5


class InputsVarbinds:

    @classmethod
    def get_set_stage_varbinds(cls, inputs_from_web: dict, stage: int = 0):
        payloads = []
        if stage == 0:
            ...

        if (inputs_from_web[MPP_MAN][InputsStructure.STATE] == '0'
            or inputs_from_web[MPP_MAN][InputsStructure.ACTUATOR] in (ActuatorAsChar.VF, ActuatorAsChar.OFF)
        ):
            payloads.append({
                key_payload: f'{inputs_prefix}{inputs_from_web[MPP_MAN][InputsStructure.INDEX]}',
                val_payload: ActuatorAsValue.ON
            })

        mpp_ph_to_set = f'{PREFIX_MAN_STAGE_PEEK}{str(stage)}'
        if (inputs_from_web[mpp_ph_to_set][InputsStructure.STATE] == '0'
            or inputs_from_web[mpp_ph_to_set][InputsStructure.ACTUATOR] in (ActuatorAsChar.VF, ActuatorAsChar.OFF)
        ):
            payloads.append({
                key_payload: f'{inputs_prefix}{inputs_from_web[mpp_ph_to_set][InputsStructure.INDEX]}',
                val_payload: ActuatorAsValue.ON
            })
        else:
            pass



        for mpp in mpp_stages_inputs:
            if mpp == mpp_ph_to_set or inputs_from_web[mpp][InputsStructure.ACTUATOR] == ActuatorAsChar.OFF:
                continue

            payloads.append({
                key_payload: f'{inputs_prefix}{inputs_from_web[mpp][InputsStructure.INDEX]}',
                val_payload: ActuatorAsValue.OFF
            })
        pprint.pprint(f'payloads: {payloads}')
        print(f'len payloads: {len(payloads)}')
        return payloads

