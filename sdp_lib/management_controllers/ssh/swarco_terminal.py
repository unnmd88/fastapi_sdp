import itertools
import os
from enum import StrEnum
from typing import Iterator

from dotenv import load_dotenv

load_dotenv()


class ItcTerminal(StrEnum):

    alias_itc = 'itc'
    alias_display = 'display'

    field_name_itc = 'itc'
    field_name_display = 'display'

    display_command = 'SIMULATE DISPLAY --poll'
    itc_command = 'itc'

    lang_uk = 'lang UK'
    l2_login = os.getenv('level2_login')
    l2_pass = os.getenv('level2_passwd')

    inp101_1 = 'inp101=0'
    inp101_0 = 'inp101=1'

    inp102_1 = 'inp102=1'
    inp102_0 = 'inp102=0'

    inp103_1 = 'inp103=1'
    inp103_0 = 'inp103=0'
    instat102 = 'instat102 ?'

    echo = 'ECHO'


login_commands = [str(ItcTerminal.lang_uk), str(ItcTerminal.l2_login,), str(ItcTerminal.l2_pass)]


def get_instat_command(instat):
    try:
        return f'instat{int(instat.split("instat")[-1])} ?'
    except ValueError:
        pass
    return f'{instat} ?'

def get_inp_command(num_inp, val):
    return f'inp{num_inp}={val}'


matches_set_stage = {
    num_stage:  f'inp{num_inp}=1' for num_stage, num_inp in zip(range(1, 9), range(104, 112))
}

reset_inputs_104_111_exclude_103 = [f'inp{num_inp}=0' for num_inp in range(4, 12)]
reset_inputs_102_111_exclude_103 = [f'inp{num_inp}=0' for num_inp in range(2, 12) if num_inp != 3]
reset_inputs_101_111 = [f'inp{num_inp}=0' for num_inp in range(1, 12)]

instat_start_102_and_display_commands = [get_instat_command('instat102'), ItcTerminal.display_command]

def get_commands_set_stage(stage: int, as_list=False, instat_start_104=None) -> list[str] | Iterator:
    if stage == 0:
        set_inp_commands = reset_inputs_102_111_exclude_103
    else:

        set_inp_commands = [ItcTerminal.inp102_1, matches_set_stage.get(stage, '')]
    if as_list:
        return [command for command in itertools.chain(login_commands, set_inp_commands)]
    else:
        return (command for command in itertools.chain(login_commands, set_inp_commands))
