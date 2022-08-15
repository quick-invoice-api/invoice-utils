import json
import pathlib
from datetime import datetime
from json import JSONDecodeError
from typing import Callable, Any


class InvoicingInputError(Exception):
    def __init__(self, file_name: str):
        super().__init__(self)
        self.__message = self._construct_message(file_name)

    def _construct_message(self, file_name):
        return f"file '{file_name}' not found"

    def __str__(self):
        return self.__message


class InvoicingInputFormatError(InvoicingInputError):
    def _construct_message(self, file_name):
        return f"file '{file_name}' not does not contain valid json"


class InvoicingEngine:
    def __init__(self, file_name: str):
        self.__validate(
            file_name,
            lambda s: s and pathlib.Path(s).exists(),
            raised=InvoicingInputError(file_name)
        )
        fpath = pathlib.Path(file_name)
        self.__validate(fpath, self.__is_file_content_valid_json, raised=InvoicingInputFormatError(fpath.name))

    @classmethod
    def __is_file_content_valid_json(cls, fpath: pathlib.Path) -> bool:
        try:
            json.loads(fpath.read_bytes())
            return True
        except JSONDecodeError:
            return False

    @classmethod
    def __validate(cls, value: Any, validation_callback: Callable[[Any], bool], raised: BaseException = None):
        if not validation_callback(value) and raised:
            raise raised

    def process(self, invoice_no: int, invoice_date: datetime):
        return {
            "header": {
                "number": invoice_no,
                "date": invoice_date,
                "customer": {},
                "emitter": {}
            },
            "details": [],
            "totals": {
                "price": 0,
                "total": 0,
                "extra": {}
            }
        }
