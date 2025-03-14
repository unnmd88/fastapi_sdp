"""
Модуль для расчёта валидной строки CmdSG конфигуратора EC-X Configurator.
"""
import json
from dataclasses import dataclass, field
from enum import StrEnum


class CmdSg(StrEnum):
    """
    В классе содержатся отображения значений для строки CmdSG  конфигуратора EC-X Configurator
    """

    GREEN = '3'
    RED = '1'
    DISABLED = '0'


@dataclass
class Intersection:
    """
    Класс данных для обработки Process конфигуратора EC-X Configurator
    """

    source_xp_data: dict[str, tuple[str, list[str]]]
    identifier: str = '-- Intersection --'
    num_stages: int = 0
    repaired_xp_data: dict[str, tuple[str, list[str]]] = field(default_factory=dict)

    def __post_init__(self):
        self.source_xp_data = dict(sorted(self.source_xp_data.items()))

    def __repr__(self):
        return self.get_pretty_output()

    def get_pretty_output(self):
        """
        Формирует строку с удобным выводом
        :return: строка с выводом информации для всех Process(xp)
        """

        pretty_output = f''
        self.num_stages = 1
        for xp, xp_data in self.repaired_xp_data.items():
            pretty_cmd_sg = self.make_pretty_cmd_sg(xp_data[1])
            curr_xp = (
                f'Process: {xp}\n'
                f'Groups in process: {xp_data[0]}\n'
                f'Groups in CmdSG repaired:\n{pretty_cmd_sg}'
            )
            pretty_output += curr_xp
        return f'{self.identifier}\nNumber of stages: {self.num_stages - 1}\n{pretty_output}'

    def make_pretty_cmd_sg(self, all_cmd_sg: list[str]) -> str:
        """
        Формирует строки CmdSG из "Process" EC-X Configurator для удобного вывода/записи в файл.
        :param all_cmd_sg: Список строк CmdSG процесса.
        :return: Удобочитаемая строка для вывода/записи в файл информации о фазах процесса,
        """

        if all_cmd_sg is not None:
            _data = ''
            for cmd_sg_stage in all_cmd_sg:
                _data += f'Stage{" " * (2 if self.num_stages < 10 else 1)}{self.num_stages}: {cmd_sg_stage}\n'
                self.num_stages += 1
            return _data

    def repair_cmd_sg_all_stages(self):
        """
        Заменяет значение группы в строке процесса CmdSG на 0, если группа не участвует в процессе
        для всех фаз процесса.
        :return: Список строк CmdSG, где индекс + 1 -> номер фазы
        """

        for xp, xp_data in self.source_xp_data.items():
            stage_in_curr_xp, cmd_sg_in_curr_xp = list(map(str, sorted(map(int, xp_data[0].split(','))))), xp_data[1]
            self.repaired_xp_data[xp] = (
                ",".join(stage_in_curr_xp), self._repair_line_stage(stage_in_curr_xp, cmd_sg_in_curr_xp)
            )

    def _repair_line_stage(self, stages_in_process: list[str], cmd_sg_all_stages_in_process: list[str]) -> list[str]:
        """
        Заменяет значение группы в строке line_stage на 0, если группа не участвует в процессе.
        :param stages_in_process: Список фаз текущего процесса.
        :param cmd_sg_all_stages_in_process: Список строк CmdSG из "Process" EC-X Configurator.
        :return: Список скорректированных строк CmdSG из "Process" EC-X Configurator.
        """

        repaired_cmd_sg_all_stages = []
        for cmd_sg_stage in cmd_sg_all_stages_in_process:
            repaired_curr_stage_cmd_sg = ",".join([
                val if str(num_group) in stages_in_process else CmdSg.DISABLED.value
                for num_group, val in enumerate(cmd_sg_stage.split(','), 1)
            ])
            repaired_cmd_sg_all_stages.append(repaired_curr_stage_cmd_sg)
        return repaired_cmd_sg_all_stages

    def write(
            self, data_for_write: list[str] | str | None = None,
            filename: str = 'repaired_CmdSG.txt',
            mode: str = 'w'
    ) -> None:
        """
        Записывает данные в файл.
        :param data_for_write: Данные, которые будут записаны в файл
        :param filename: Имя файла
        :param mode: Режим записи
        :return: None
        """

        data_for_write = data_for_write or self.get_pretty_output()
        with open(filename, mode) as f:
            if isinstance(data_for_write, str):
                f.write(data_for_write)
            elif isinstance(data_for_write, list):
                for line in data_for_write:
                    f.write(f'{line}\n')
            else:
                raise TypeError('Данные для записи в файл должны быть строкой или списком')


if __name__ == '__main__':
    from toolkit.sdp_lib.utils_common import write_data_to_file

    groups_in_xp1 = '1,4,20,22,23,29,30,32,34,35,42,44,45,46,49,50,51,52,53,54,55,56,57,58,59,60'
    xp1_cmd_sg = [
        '3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,1,1,1,1,1,1,1,1,3,1,1,1,1,3,3,1,1,1,1,1,1,1,1,1,1,3,1,1,3,1,1,1,1,1,1,1,1,1,1,1',
        '3,1,1,3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,3,1,1,1,3,3,1,1,1,1,1,1,1,1,1,3,1,1,1,1,3,1,1,1,1,1,1,1,1,1,1',
        '3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,1,1,1,1,1,1,1,1,3,1,1,1,1,3,3,1,1,1,1,1,1,1,1,1,1,3,1,1,1,1,3,1,1,1,1,1,1,1,1,1',
        '3,1,1,3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,3,1,1,1,3,3,1,1,1,1,1,1,1,1,1,3,1,1,1,1,1,1,3,1,1,1,1,1,1,1,1',
        '3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,1,1,1,1,1,1,1,1,3,1,1,1,1,3,3,1,1,1,1,1,1,1,1,1,1,3,1,1,1,1,1,1,3,1,1,1,1,1,1,1',
        '1,1,1,3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,1,1,1,1,1,1,1,3,1,3,1,1,1,1,1,1,1,1,1,3,1,3,3,1,1,1,1,1,1,1,1,3,1,1,1,1,1,1',
        '1,1,1,3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,3,1,1,1,1,1,1,1,1,3,1,1,1,1,1,1,1,1,1,3,1,1,3,1,1,1,1,1,1,1,1,1,3,1,1,1,1,1',
        '3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,1,1,1,1,1,1,1,1,3,1,1,1,1,3,3,1,1,1,1,1,1,1,1,1,1,3,1,1,1,1,1,1,1,1,1,3,1,1,1,1',
        '1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,1,1,1,1,1,1,1,1,3,1,1,1,1,3,1,1,1,1,1,1,1,1,1,1,1,3,1,1,1,1,1,1,1,1,1,1,3,1,1,1',
        '3,1,1,3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,3,1,1,1,3,3,1,1,1,1,1,1,1,1,1,3,1,1,1,1,1,1,1,1,1,1,1,1,3,1,1',
        '3,1,1,3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,1,1,1,1,1,1,1,1,1,1,3,1,1,1,1,1,1,1,3,1,1,3,1,1,1,1,1,1,1,1,1,1,1,1,1,3,1',
        '1,1,1,3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,3,1,1,1,1,1,1,1,1,3,1,1,1,1,1,1,1,1,1,3,1,1,3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3',
    ]
    groups_in_xp2 = '2,12,13,14,15,31,33,41'
    xp2_cmd_sg = [
            '1,1,1,1,1,1,1,1,1,1,1,1,3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,1,3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1',
            '1,3,1,1,1,1,1,1,1,1,1,3,1,3,3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1',
            '1,1,1,1,1,1,1,1,1,1,1,1,1,3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,1,3,1,1,1,1,1,1,1,3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1',
            '1,3,1,1,1,1,1,1,1,1,1,1,1,3,3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1',
            '1,3,1,1,1,1,1,1,1,1,1,3,3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1',
    ]
    groups_in_xp3 = '9,27,37'
    xp3_cmd_sg = [
        '1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,1,1,1,1,1,1,1,1,1,3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1',
        '1,1,1,1,1,1,1,1,3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1',
        '1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1',
        '1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1',
    ]
    groups_in_xp4 = '3,5,6,7,8,10,11,16,17,18,19,21,24,25,26,28,36,38,39,40,43,47,48'
    xp4_cmd_sg = [
        '1,1,3,1,1,1,3,3,1,3,3,1,1,1,1,3,1,1,1,1,3,1,1,1,3,1,1,1,1,1,1,1,1,1,1,3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1',
        '1,1,3,1,1,1,3,3,1,1,3,1,1,1,1,3,3,3,1,1,3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1',
        '1,1,3,1,3,1,1,1,1,1,3,1,1,1,1,3,3,3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,1,1,1,1,1,1,3,1,1,1,3,3,1,1,1,1,1,1,1,1,1,1,1,1',
        '1,1,1,1,1,3,3,3,1,3,3,1,1,1,1,1,1,1,1,1,3,1,1,1,3,3,1,1,1,1,1,1,1,1,1,1,1,3,3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1',
        '1,1,1,1,3,3,1,1,1,3,1,1,1,1,1,1,1,3,3,1,1,1,1,1,1,3,1,1,1,1,1,1,1,1,1,1,1,3,3,3,1,1,3,1,1,1,3,3,1,1,1,1,1,1,1,1,1,1,1,1',
        '1,1,3,1,1,1,1,1,1,3,3,1,1,1,1,3,1,1,1,1,3,1,1,3,3,1,1,1,1,1,1,1,1,1,1,3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1',
        '1,1,3,1,1,3,1,1,1,3,3,1,1,1,1,1,1,1,1,1,3,1,1,3,3,1,1,1,1,1,1,1,1,1,1,3,1,1,3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1',
        '1,1,1,1,3,3,1,1,1,3,1,1,1,1,1,1,1,3,3,1,1,1,1,1,1,3,1,1,1,1,1,1,1,1,1,1,1,3,3,3,1,1,3,1,1,1,3,3,1,1,1,1,1,1,1,1,1,1,1,1',
        '1,1,3,1,1,1,3,3,1,3,1,1,1,1,1,3,1,1,3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1',
        '1,1,1,1,1,3,3,3,1,3,1,1,1,1,1,1,1,1,1,1,3,1,1,1,3,3,1,1,1,1,1,1,1,1,1,1,1,3,3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1',
        '1,1,1,1,1,3,3,3,1,1,3,1,1,1,1,1,3,3,1,1,3,1,1,1,1,3,1,1,1,1,1,1,1,1,1,1,1,3,3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1',
    ]


    all_intersections = {
        '1': (groups_in_xp1, xp1_cmd_sg),
        '2': (groups_in_xp2, xp2_cmd_sg),
        '3': (groups_in_xp3, xp3_cmd_sg),
        '4': (groups_in_xp4, xp4_cmd_sg),
    }

    intersection = Intersection(all_intersections, 'СО 413 Тверская застава')
    intersection.repair_cmd_sg_all_stages()
    print(intersection)
    write_data_to_file(data_for_write=intersection.get_pretty_output(), filename='repaired_CmdSG.txt')
    write_data_to_file(json.dumps(intersection.repaired_xp_data, indent=4), filename='data.json')

