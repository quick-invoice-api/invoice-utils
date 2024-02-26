from datetime import datetime
from decimal import Decimal

from invoice_utils.engine import *
from invoice_utils.models import *


def test_process_empty_input_data_outputs_base_invoice_document_structure(
        resolve_path,
):
    expected_invoice_no = 1
    expected_invoice_date = datetime(2022, 1, 15, 13, 14, 15)

    output = InvoicingEngine([{}]).process(
        expected_invoice_no, expected_invoice_date
    )

    assert output == {
        "header": {
            "number": expected_invoice_no,
            "date": expected_invoice_date,
            "currency": {},
            "buyer": {},
            "seller": {},
        },
        "items": [],
        "totals": {"price": 0, "total": 0, "extra": {}},
    }


def test_process_header_rule_outputs_correct_buyer_and_seller_information(
    test_basic_rules
):
    expected_invoice_no = 1
    expected_invoice_date = datetime(2022, 1, 15, 13, 14, 15)

    output = InvoicingEngine(test_basic_rules).process(
        expected_invoice_no, expected_invoice_date
    )

    assert output["header"]["buyer"] == {
        "name": "Invoiced Customer Ltd",
        "address": "Buyer Street, 10",
        "bank": {"iban": "ABC", "name": "Buyer Test Bank"},
    }
    assert output["header"]["seller"] == {
        "name": "Invoicing Company Ltd",
        "address": "Seller's Lane, Building C, Floor 1, Room 433",
        "bank": {"iban": "DEF", "name": "Seller Test Bank"},
    }


def test_process_currency_rule_outputs_currency_in_invoice_header(test_basic_rules):
    output = InvoicingEngine(test_basic_rules).process(
        1, datetime(2022, 1, 15, 13, 14, 15)
    )

    assert output["header"]["currency"] == {
        "main": "XYZ",
        "exchangeRates": {"ABC": 1.15},
    }


def test_process_one_item_computes_item_price_correctly(test_basic_rules):
    item = InvoicedItem(text="test item", quantity=2.71828182, unit_price=3.14159265)

    output = InvoicingEngine(test_basic_rules).process(
        1, datetime(2022, 1, 15, 13, 14, 15), [item]
    )

    assert len(output["items"]) == 1
    assert output["items"][0]["item_no"] == 1
    assert output["items"][0]["currency"] == "XYZ"
    assert output["items"][0]["text"] == "test item"
    assert output["items"][0]["quantity"] == Decimal("2.718282")
    assert output["items"][0]["unit_price"] == Decimal("3.141593")
    assert output["items"][0]["item_price"] == Decimal("8.539736")


def test_process_one_item_computes_extra_currencies(test_basic_rules):
    item = InvoicedItem(text="test item", quantity=2.71828182, unit_price=3.14159265)

    output = InvoicingEngine(test_basic_rules).process(
        1, datetime(2022, 1, 15, 13, 14, 15), [item]
    )

    assert len(output["items"]) == 1
    assert len(output["items"][0]["extra"]["currencies"]) == 1

    item_in_currency = output["items"][0]["extra"]["currencies"][0]
    assert item_in_currency["currency"] == "ABC"
    assert item_in_currency["unit_price"] == Decimal("3.612832")
    assert item_in_currency["item_price"] == Decimal("9.820696")
