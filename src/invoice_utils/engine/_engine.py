import json
import pathlib
from datetime import datetime
from decimal import Decimal
from json import JSONDecodeError

from invoice_utils.models import InvoicedItem
from invoice_utils.engine._errors import InvoicingInputError, InvoicingInputFormatError


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

    def _process_item(self, item_no: int, item_tax: Decimal, item: InvoicedItem):
        items = self.__invoice.get("items", [])

        currency_info = self.__invoice["header"]["currency"]
        qty = round(Decimal(item.quantity), 6)
        unit_price = round(Decimal(item.unit_price), 6)
        item_price = round(qty * unit_price, 6)

        extra_currencies = []
        for currency, rate in currency_info.get("exchangeRates", {}).items():
            dec_rate = round(Decimal(rate), 6)
            up_currency = round(unit_price * dec_rate, 6)
            ip_currency = round(qty * up_currency, 6)
            it_currency = round(item_tax * dec_rate, 6)
            extra_currencies.append(
                {
                    "currency": currency,
                    "unit_price": str(up_currency),
                    "item_price": str(ip_currency),
                    "item_tax": str(it_currency),
                    "item_total": str(ip_currency + it_currency),
                }
            )
        items.append(
            {
                "item_no": item_no,
                "currency": currency_info["main"],
                "text": item.text,
                "quantity": str(qty),
                "unit_price": str(unit_price),
                "item_price": str(item_price),
                "item_tax": str(item_tax),
                "item_total": str(item_price + item_tax),
                "extra": {
                    "currencies": extra_currencies
                }
            }
        )
        self.__invoice["items"] = items

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
            vat = round(Decimal(0.19) * Decimal(item.unit_price) * Decimal(item.quantity), 6)
            self._process_item(index + 1, vat, item)

        return self.__invoice
