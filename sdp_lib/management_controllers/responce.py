from enum import StrEnum


class FieldsNames(StrEnum):

    protocol_snmp = 'snmp'
    protocol_http = 'http'
    web_content = 'web_content'
    source = 'source'
    curr_stage = 'stage'
    num_detectors = 'num_detectors'
    status_soft_flag180_181 = 'status_soft_flag180_181'
    curr_plan = 'curr_plan'
    curr_mode = 'curr_mode'
    curr_status = 'curr_status'

    power_up = 'powerUp'
    dark = 'dark'
    flash = 'flash'
    three_light = '3_light'
    all_red = 'all_red'

    red_yellow_green = 'red_yellow_green'