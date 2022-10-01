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

        taxes = []
        extra_ops = [ rule for rule in self.__rules if rule.get("type") == "item_op" ]
        for op_info in extra_ops:
            op = op_info["operation"]
            val = Decimal(op_info["value"])
            name = op_info["name"]
            if op == "*":
                taxes.append({
                    "name": name,
                    "value": round(val * item_price, 6),
                })
            elif op == "+":
                taxes.append({
                    "name": name,
                    "value": round(val + item_price, 6)
                })
        item_tax = round(sum(Decimal(tax["value"]) for tax in taxes), 6)
        extra_currencies = []
        for currency, rate in currency_info.get("exchangeRates", {}).items():
            dec_rate = round(Decimal(rate), 6)
            up_currency = round(unit_price * dec_rate, 6)
            ip_currency = round(qty * up_currency, 6)
            currency_taxes = []
            for tax in taxes:
                currency_taxes.append({
                    "name": tax["name"],
                    "value": round(Decimal(tax["value"]) * dec_rate, 6),
                })
            it_currency = round(sum(Decimal(tax["value"]) for tax in currency_taxes), 6)
            extra_currencies.append(
                {
                    "currency": currency,
                    "unit_price": up_currency,
                    "item_price": ip_currency,
                    "item_total": ip_currency + it_currency,
                    "taxes": currency_taxes
                }
            )

        items.append(
            {
                "item_no": item_no,
                "currency": currency_info["main"],
                "text": item.text,
                "quantity": qty,
                "unit_price": unit_price,
                "item_price": item_price,
                "item_total": item_price + item_tax,
                "taxes": taxes,
                "extra": {
                    "currencies": extra_currencies,
                }
            }
        )
        self.__invoice["items"] = items

    def _compute_totals(self, input_items: list[dict]):
        result = {
            "price": sum(map(lambda i: i["item_price"], input_items)),
            "total": sum(map(lambda i: i["item_total"], input_items)),
        }
        tax_totals = {}
        for item in self.__invoice["items"]:
            for tax in item["taxes"]:
                current_value = Decimal(tax_totals.get(tax["name"], 0))
                current_value += Decimal(tax["value"])
                tax_totals[tax["name"]] = current_value
        if tax_totals:
            result["taxes"] = [
                {
                    "name": tax,
                    "value": value,
                } for tax, value in tax_totals.items()
            ]
        return result

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
        main_currency_totals = self._compute_totals(self.__invoice["items"])
        self.__invoice["totals"].update(main_currency_totals)

        return self.__invoice
