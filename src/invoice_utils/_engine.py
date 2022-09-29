import json
import pathlib
from datetime import datetime
from decimal import Decimal
from json import JSONDecodeError

from invoice_utils._adt import InvoicedItem


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
            "header": {"buyer": {}, "currency": {}, "seller": {}},
            "items": [],
            "totals": {"price": 0, "total": 0, "extra": {}},
        }

    def _process_item(self, item_no: int, item: InvoicedItem):
        items = self.__invoice["items"]
        currency_info = self.__invoice["header"]["currency"]
        item_price = item.quantity * item.unit_price

        # main currency
        items.append(
            {
                "item_no": item_no,
                "currency": currency_info["main"],
                "text": item.text,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "item_price": item_price,
                "tax": 0,
                "item_total": item_price,
            }
        )

        for currency, rate in currency_info.get("exchangeRates", {}).items():
            dec_rate = round(Decimal(rate), 6)
            item_price_currency = item.quantity * item.unit_price * dec_rate
            items.append(
                {
                    "item_no": item_no,
                    "currency": currency,
                    "text": item.text,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price * dec_rate,
                    "item_price": item_price_currency,
                    "tax": 0,
                    "item_total": item_price_currency,
                }
            )

    def process(
        self, invoice_no: int, invoice_date: datetime, items: list[InvoicedItem] = None
    ):
        items = items or []
        header = self.__invoice["header"]
        header["number"] = invoice_no
        header["date"] = invoice_date

        header_rules = [
            rule for rule in self.__rules if rule.get("type", "") == "header"
        ]
        header["buyer"] = header_rules[0]["buyer"] if len(header_rules) > 0 else {}
        header["seller"] = header_rules[0]["seller"] if len(header_rules) > 0 else {}

        currency_rules = [
            rule for rule in self.__rules if rule.get("type", "") == "currency"
        ]
        if len(currency_rules) > 0:
            rule = currency_rules[0]
            main_currency = rule.get("main", {}).get("symbol", "")
            secondary_currencies = rule.get("secondary", [])
            exchange_rates = {
                currency.get("symbol", f"currency-{index}"): currency.get("rate", 1.0)
                for index, currency in enumerate(secondary_currencies)
            }
            header["currency"] = {
                "main": main_currency,
                "exchangeRates": exchange_rates,
            }
        for index, item in enumerate(items):
            self._process_item(index + 1, item)

        return self.__invoice
