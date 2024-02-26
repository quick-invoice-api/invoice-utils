import json
import pathlib
from datetime import datetime
from decimal import Decimal
from json import JSONDecodeError
from logging import getLogger
from typing import Optional

from invoice_utils.models import InvoicedItem
from invoice_utils.engine._errors import InvoicingInputError, InvoicingInputFormatError

from ._currency import BnrFxRateRule, CurrencyRule
from ._header import HeaderRule


class InvoicingEngine:
    def __init__(self, rules: list[dict]):
        self._log = getLogger(self.__class__.__name__)
        self.__rules = rules
        self.__init_invoice()

    def __init_invoice(self):
        self.__invoice = {
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
        # TODO: This line overwrites the item_tax mandatory parameter received
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
                "currency": currency_info.get("main", ""),
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
        for item in input_items:
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
        self.__init_invoice()
        items = items or []

        for process_rule in [
            HeaderRule(self.__invoice, self.__rules, invoice_no, invoice_date),
            CurrencyRule(self.__invoice, self.__rules),
            BnrFxRateRule(self.__invoice, self.__rules, invoice_date),
        ]:
            process_rule()

        for index, item in enumerate(items):
            vat = round(Decimal(0.19) * Decimal(item.unit_price) * Decimal(item.quantity), 6)
            self._process_item(index + 1, vat, item)
        main_currency_totals = self._compute_totals(self.__invoice["items"])
        self.__invoice["totals"].update(main_currency_totals)

        items_by_currency = {}
        for item in self.__invoice["items"]:
            extra_currencies = item["extra"]["currencies"]
            for sub_item in extra_currencies:
                key = sub_item["currency"]
                same_currency_items = items_by_currency.get(key, [])
                same_currency_items.append(sub_item)
                items_by_currency[key] = same_currency_items
        if len(items_by_currency) > 0:
            total_in_currencies = []
            for currency, currency_items in items_by_currency.items():
                currency_totals = self._compute_totals(currency_items)
                currency_totals["currency"] = currency
                total_in_currencies.append(currency_totals)
            self.__invoice["totals"]["extra"]["currencies"] = total_in_currencies

        return self.__invoice
