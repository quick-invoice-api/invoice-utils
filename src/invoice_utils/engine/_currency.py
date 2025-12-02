from datetime import datetime, timedelta
from decimal import Decimal
from logging import getLogger
from typing import Callable
from xml.etree import ElementTree as Etree

import requests
from arrow import utcnow


class BaseCurrencyRule(Callable):
    def __init__(self, invoice: dict):
        self._invoice = invoice

    def _set_currency_info(self, main, rates, date=None):
        currency_info: dict = self._invoice["header"].get("currency", {})
        currency_info.update({
            "main": main,
            "exchangeRates": rates,
        })
        if date is not None:
            currency_info["date"] = date
        self._invoice["header"]["currency"] = currency_info


class CurrencyRule(BaseCurrencyRule):
    def __init__(self, invoice: dict, rules: list[dict]):
        super().__init__(invoice)
        self._rules = rules

    def __call__(self):
        rule = next(
            filter(lambda r: r.get("type") == "currency", self._rules), None
        )
        if rule is None:
            return

        main_currency = rule.get("main", {}).get("symbol", "")
        secondary_currencies = rule.get("secondary", [])
        exchange_rates = {
            currency.get("symbol", f"currency-{index}"): currency.get("rate", 1.0)
            for index, currency in enumerate(secondary_currencies)
        }
        self._set_currency_info(main_currency, exchange_rates)


class BnrFxRateRule(BaseCurrencyRule):
    def __init__(self, invoice: dict, rules: list[dict], invoice_date: datetime):
        super().__init__(invoice)
        self._log = getLogger(self.__class__.__name__)
        self._invoice = invoice
        self._rules = rules
        days_from_friday = invoice_date.weekday() - 4
        self.__invoice_date = (
            invoice_date - timedelta(days=days_from_friday)
            if days_from_friday > 0
            else invoice_date
        )

    def __call__(self):
        bnr_rule = next(
            filter(lambda rule: rule.get("type", "") == "bnr-fx-rate", self._rules),
            None
        )
        if bnr_rule is None:
            return
        rates = {}
        symbol = bnr_rule.get("symbol", "RON")
        bnr_fx_date = None
        try:
            res = requests.get(
                f"https://bnr.ro/files/xml/years/nbrfxrates{self.__invoice_date.year}.xml",
                headers={"Accept": "text/xml", "Accept-Encoding": "utf-8"}
            )
            root = Etree.fromstring(res.text)
            bnr_date_format = "%Y-%m-%d"
            invoice_date_str = self.__invoice_date.strftime(bnr_date_format)
            date_rates = None
            min_days = 20
            for cube_node in root.findall(".//{http://www.bnr.ro/xsd}Cube"):
                bnr_fx_date = cube_node.attrib.get("date")
                if bnr_fx_date is None:
                    continue
                bnr_fx_date = datetime.strptime(bnr_fx_date, bnr_date_format)
                date_diff = abs((bnr_fx_date - self.__invoice_date.replace(tzinfo=None)).days)
                if date_diff < min_days:
                    min_days = date_diff
                    date_rates = cube_node
            if date_rates is None:
                self._log.info("can't find BNR fx rates for %s", invoice_date_str)
                return
            if min_days > 0 and bnr_fx_date is not None:
                self._log.info("found BNR fx rate for %s, not %s", bnr_fx_date.strftime("%Y-%m-%d"), invoice_date_str)

            rate = next(iter(date_rates.findall(f"{{http://www.bnr.ro/xsd}}Rate[@currency='{symbol}']")))
            rates["RON"] = Decimal(rate.text)
        except StopIteration:
            self._log.info("couldn't find BNR fx rate for symbol %s", symbol)
        except Etree.ParseError:
            self._log.warning("invalid XML downloaded from BNR")
        except Exception as exc:
            self._log.error("download error on BNR fx-rates", exc_info=exc)
        finally:
            self._set_currency_info(symbol, rates, bnr_fx_date)
