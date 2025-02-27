from enum import StrEnum


class FieldsNames(StrEnum):

    protocol_snmp = 'snmp'
    protocol_stcip = 'stcip'
    protocol_ug405 = 'ug405'
    protocol_utmc = 'utmc'
    protocol_http = 'http'
    web_content = 'web_content'
    source = 'source'

    curr_stage = 'current_stage'
    num_detectors = 'num_detectors'
    status_soft_flag180_181 = 'status_soft_flag180_181'
    curr_plan = 'current_plan'
    curr_mode = 'current_mode'
    curr_status = 'current_status'
    curr_status_mode = 'curr_status_mode'
    plan_source = 'plan_source'
    fixed_time_status = 'fixed_time_status'

    bit_TO = 'TO_bit'
    operation_mode = 'operation_mode'

    power_up = 'powerUp'
    dark = 'dark'
    flash = 'flash'
    three_light = '3_light'
    all_red = 'all_red'

    red_yellow_green = 'red_yellow_green'