import collections
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


matches_actuators = {
    ActuatorAsChar.VF: ActuatorAsValue.VF,
    ActuatorAsChar.OFF: ActuatorAsValue.OFF,
    ActuatorAsChar.ON: ActuatorAsValue.ON,
    ActuatorAsValue.VF: ActuatorAsChar.VF,
    ActuatorAsValue.OFF: ActuatorAsChar.OFF,
    ActuatorAsValue.ON: ActuatorAsChar.ON
}

def convert_actuator_val_to_actuator_char(val):
    pass

def convert_actuator_char_to_actuator_val(char):
    try:
        ActuatorAsChar(char)
        return
    except ValueError:
        return None

def get_actuator_val_for_payload(value):
    if value in [el for el in ActuatorAsValue]:
        return value
    elif value in [el for el in ActuatorAsChar]:
        return matches_actuators.get(value)
    else:
        raise ValueError(f'Некорректное значение актуатора: {value!r}')



class InputsStructure(IntEnum):

    INDEX     = 0
    NUM       = 1
    NAME      = 2
    STATE     = 3
    TIME      = 4
    ACTUATOR  = 5


T_inp_props = tuple[str, str, str, str, str]
T_inps_container = list[tuple[str, str]] | tuple[tuple[str, str], ...] | dict[str, str]


class InputsVarbinds:

    def __init__(self, inputs_from_web: dict[str, T_inp_props] = None):
        self._inputs_from_web = None
        self._mpp_man_index = None
        self._mpp_man_state = None
        self._mpp_man_actuator = None
        self.set_inputs_from_web_data(inputs_from_web)

    def set_inputs_from_web_data(self, inputs_from_web):
        self._inputs_from_web = inputs_from_web
        if self._inputs_from_web is not None:
            self._mpp_man_index = self._inputs_from_web[MPP_MAN][InputsStructure.INDEX]
            self._mpp_man_state = self._inputs_from_web[MPP_MAN][InputsStructure.STATE]
            self._mpp_man_actuator = self._inputs_from_web[MPP_MAN][InputsStructure.ACTUATOR]

    def get_varbinds_as_from_name(
            self,
            data: T_inps_container
    ):

        payloads = []

        if isinstance(data, dict):
            data = data.items()

        for inp_name, actuator_val in data:
            if (inp_name in self._inputs_from_web
                and self._inputs_from_web[inp_name][InputsStructure.ACTUATOR] != actuator_val
            ):
                payloads.append(
                    self.create_payload(self._inputs_from_web[inp_name][InputsStructure.INDEX], actuator_val)
                )
        return payloads

    def get_varbinds_set_stage(self, stage: int = 0):

        # self._payloads_deque = collections.deque()

        if stage == 0:
            return self.get_varbinds_reset_man()
        elif stage in range(1, 9):
            return self._get_varbinds_set_stage(stage)

    def _get_varbinds_set_stage(self, stage: int):
        payloads = collections.deque()
        if self._mpp_man_state == '0' or self._mpp_man_actuator in (ActuatorAsChar.VF, ActuatorAsChar.OFF):
            payloads.append(
                self.create_payload(self._mpp_man_index, ActuatorAsValue.ON)
            )

        stage = str(stage)
        mpp_ph_to_set = f'{PREFIX_MAN_STAGE_PEEK}{stage}'
        for mpp in mpp_stages_inputs:
            if (mpp != mpp_ph_to_set
                and self._inputs_from_web[mpp][InputsStructure.ACTUATOR] != ActuatorAsChar.OFF
            ):
                payloads.append(
                    self.create_payload(self._inputs_from_web[mpp][InputsStructure.INDEX], ActuatorAsValue.OFF)
                )
        if self._inputs_from_web[mpp_ph_to_set][InputsStructure.ACTUATOR] != ActuatorAsChar.ON:
            payloads.append(
                self.create_payload(self._inputs_from_web[mpp_ph_to_set][InputsStructure.INDEX], ActuatorAsValue.ON)
            )
        return payloads

    def get_varbinds_reset_man(self):
        payloads = collections.deque()
        if (self._inputs_from_web[MPP_MAN][InputsStructure.STATE] == '1'
            or self._inputs_from_web[MPP_MAN][InputsStructure.ACTUATOR] == ActuatorAsChar.ON
        ):
            payloads.append(
                self.create_payload(self._inputs_from_web[MPP_MAN][InputsStructure.INDEX], ActuatorAsValue.OFF)
            )

        for mpp_inp in mpp_stages_inputs:
            # if (self._inputs_from_web[mpp_inp][InputsStructure.STATE] == '1'
            #    or self._inputs_from_web[mpp_inp][InputsStructure.ACTUATOR] != ActuatorAsChar.VF
            # ):
            if self._inputs_from_web[mpp_inp][InputsStructure.ACTUATOR] != ActuatorAsChar.VF:
                payloads.append(
                    self.create_payload(self._inputs_from_web[mpp_inp][InputsStructure.INDEX], ActuatorAsValue.VF)
                )
        return payloads

    def create_payload(self, inp_index: str, actuator_val: ActuatorAsValue | str) -> tuple:

        return (
            (key_payload, f'{inputs_prefix}{inp_index}'),
            (val_payload, get_actuator_val_for_payload(actuator_val))
        )

