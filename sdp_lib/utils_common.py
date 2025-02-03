import ipaddress
from datetime import datetime as dt


def set_curr_datetime(sep: str = ':') -> str:
    """
    Возвращает текущую дату и время
    :param sep: разделитель между датой и временем
    :return: отформатированная строка с датой и временем
    """

    return dt.today().strftime(f"%Y-%m-%d %H{sep}%M{sep}%S")


def reverse_slashes(path: str) -> str:
    """
    Разворачивает слеши c "\" или "\\" на "/" пути path
    :param path: строка с путём, в которой необходимо развернуть слеши
    :return: строка - path с развёрнутыми слешами
    """

    return path.replace('\\', '/')


def write_data_to_file(data_for_write: list[str] | str, filename: str, mode: str = 'w') -> None:
    """
    Записывает данные в файл.
    :param data_for_write: Данные, которые будут записаны в файл
    :param filename: Имя файла
    :param mode: Режим записи
    :return: None
    """

    with open(filename, mode) as f:
        if isinstance(data_for_write, str):
            f.write(data_for_write)
        elif isinstance(data_for_write, list):
            for line in data_for_write:
                f.write(f'{line}\n')
        else:
            raise TypeError('Данные для записи в файл должны быть строкой или списком')


def check_ipv4(ip: str) -> bool | None:
    try:
        ipaddress.IPv4Address(ip)
        return True
    except ipaddress.AddressValueError:
        return False
