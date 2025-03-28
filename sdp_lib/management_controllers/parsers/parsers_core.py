import abc
from typing import Any


class Parsers(metaclass=abc.ABCMeta):

    def __init__(self, content: Any):
        self.content = content
        self.parsed_content_as_dict = {}
        self.data_for_response: dict[str, Any] | None = None

    @abc.abstractmethod
    def parse(self) -> dict[str, Any]:
        ...


