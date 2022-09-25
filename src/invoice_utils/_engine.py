import json
import pathlib
from datetime import datetime
from json import JSONDecodeError
from typing import Callable, Any, Union


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
        if not file_name:
            raise InvoicingInputError(file_name)
        fpath = pathlib.Path(file_name)
        if not fpath.exists():
            raise InvoicingInputError(file_name)

        try:
            self.__rules: list[dict] = json.loads(fpath.read_bytes())
        except JSONDecodeError as ex:
            raise InvoicingInputFormatError(fpath.name) from ex

        self.__invoice = {
            "header": {
                "buyer": {},
                "seller": {}
            },
            "details": [],
            "totals": {
                "price": 0,
                "total": 0,
                "extra": {}
            }
        }

    def process(self, invoice_no: int, invoice_date: datetime):
        header = self.__invoice["header"]
        header["number"] = invoice_no
        header["date"] = invoice_date

        header_rules = [rule for rule in self.__rules if rule.get("type", "") == "header"]
        header["buyer"] = header_rules[0]["buyer"] if len(header_rules) > 0 else {}
        header["seller"] = header_rules[0]["seller"] if len(header_rules) > 0 else {}
        return self.__invoice
