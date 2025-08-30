from datetime import datetime
from decimal import Decimal

from invoice_utils.engine import InvoicingEngine
from invoice_utils.models import InvoicedItem


def test_process_tax_rule(basic_rules):
    engine = InvoicingEngine(basic_rules)

    output = engine.process(
        1, datetime.now(), [InvoicedItem("test", Decimal(2), Decimal(5))]
    )

    assert len(output["items"]) == 1
    assert output["items"][0]["taxes"] == [{
        "name": "vat",
        "value": Decimal("2.000000")
    }]
    assert output["items"][0]["extra"]["currencies"][0]["taxes"] == [{
        "name": "vat",
        "value": Decimal("2.300000")
    }]
    assert output["items"][0]["item_total"] == Decimal("12.000000")


def test_process_computes_total_taxes(basic_rules):
    engine = InvoicingEngine(basic_rules)

    output = engine.process(
        1, datetime.now(), [InvoicedItem("test", Decimal(2), Decimal(5))]
    )

    assert "taxes" in output["totals"]
    assert output["totals"]["taxes"] == [{
         "name": "vat",
         "value": Decimal("2.0")
    }]
