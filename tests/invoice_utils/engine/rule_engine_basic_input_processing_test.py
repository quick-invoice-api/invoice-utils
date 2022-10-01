from datetime import datetime

from invoice_utils.engine import *
from invoice_utils.models import *


def test_process_empty_input_data_outputs_base_invoice_document_structure(
    input_data_resolver,
):
    expected_invoice_no = 1
    expected_invoice_date = datetime(2022, 1, 15, 13, 14, 15)

    output = InvoicingEngine(input_data_resolver("empty.json")).process(
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
    input_data_resolver,
):
    expected_invoice_no = 1
    expected_invoice_date = datetime(2022, 1, 15, 13, 14, 15)

    output = InvoicingEngine(input_data_resolver("basic.json")).process(
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


def test_process_currency_rule_outputs_currency_in_invoice_header(input_data_resolver):
    output = InvoicingEngine(input_data_resolver("basic.json")).process(
        1, datetime(2022, 1, 15, 13, 14, 15)
    )

    assert output["header"]["currency"] == {
        "main": "XYZ",
        "exchangeRates": {"ABC": 1.15},
    }


def test_process_one_item_with_basic_template(input_data_resolver):
    item = InvoicedItem(text="test item", quantity=2.71828182, unit_price=3.14159265)

    output = InvoicingEngine(input_data_resolver("basic.json")).process(
        1, datetime(2022, 1, 15, 13, 14, 15), [item]
    )

    assert output["items"] == [
        {
            "item_no": 1,
            "currency": "XYZ",
            "text": "test item",
            "quantity": "2.718282",
            "unit_price": "3.141593",
            "item_price": "8.539736",
            "item_tax": "1.622549",
            "item_total": "10.162285",
            "extra": {
                "currencies": [{
                    "currency": "ABC",
                    "unit_price": "3.612832",
                    "item_price": "9.820696",
                    "item_tax": "1.865931",
                    "item_total": "11.686627",
                }]
            }
        }
    ]
