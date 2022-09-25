from datetime import datetime

from invoice_utils import InvoicingEngine


def test_process_empty_input_data_outputs_base_invoice_document_structure(input_data_resolver):
    expected_invoice_no = 1
    expected_invoice_date = datetime(2022, 1, 15, 13, 14, 15)

    output = InvoicingEngine(input_data_resolver("basic.json")).process(
        expected_invoice_no, expected_invoice_date
    )

    assert output == {
        "header": {
            "number": expected_invoice_no,
            "date": expected_invoice_date,
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


def test_process_header_rule_outputs_correct_buyer_and_seller_information(input_data_resolver):
    expected_invoice_no = 1
    expected_invoice_date = datetime(2022, 1, 15, 13, 14, 15)

    output = InvoicingEngine(input_data_resolver("one_line.json")).process(
        expected_invoice_no, expected_invoice_date
    )

    assert output["header"]["buyer"] == {
        "name": "Invoiced Customer Ltd",
        "address": "Buyer Street, 10",
        "bank":
        {
            "iban": "ABC",
            "name": "Buyer Test Bank"
        }
    }
    assert output["header"]["seller"] == {
        "name": "Invoicing Company Ltd",
        "address": "Seller's Lane, Building C, Floor 1, Room 433",
        "bank":
        {
            "iban": "DEF",
            "name": "Seller Test Bank"
        }
    }
