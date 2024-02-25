from datetime import datetime
from typing import Callable


class HeaderRule(Callable):
    def __init__(self, invoice: dict, rules: list[dict], invoice_no: int, invoice_date: datetime):
        self._invoice = invoice
        self._rules = rules
        self._invoice_no = invoice_no
        self._invoice_date = invoice_date

    def __call__(self):
        invoice_header = {
            "number": self._invoice_no,
            "date": self._invoice_date,
            "currency": {},
        }
        header_rules = [
            rule for rule in self._rules if rule.get("type", "") == "header"
        ]
        invoice_parties = header_rules[0] if len(header_rules) > 0 else {
            "buyer": {}, "seller": {}
        }
        invoice_header.update(invoice_parties)
        self._invoice.update({"header": invoice_header})

