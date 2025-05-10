from enum import StrEnum


class AllowedControllers(StrEnum):

    SWARCO = 'Swarco'
    POTOK_P = 'Поток (P)'
    POTOK_S = 'Поток (S)'
    PEEK = 'Peek'


class AllowedDataHostFields(StrEnum):
    errors = 'errors'
    host_id = 'host_id'
    type_controller = 'type_controller'
    scn = 'scn'
    database = 'database'

    source_data = 'source_data'
    results = 'results'
    execution_time = 'execution_time'
    ip_or_name_from_user = 'ip_or_name_from_user'
    entity = 'entity'
    ip_adress = 'ip_adress'
    ipv4 = 'ip_address'
    ip_or_name = 'ip/name'
    option = 'option'
    #Database entity
    search_in_db = 'search_in_db'
    search_in_db_field = 'search_in_db_field'
    found = 'found'
    count = 'count'
    db_records = 'db_records'
    #management
    command = 'command'
    value = 'value'



