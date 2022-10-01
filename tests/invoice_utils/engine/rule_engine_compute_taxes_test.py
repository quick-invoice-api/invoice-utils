from datetime import datetime
from decimal import Decimal

from invoice_utils.engine import InvoicingEngine
from invoice_utils.models import InvoicedItem


def test_process_tax_rule(input_data_resolver):
    engine = InvoicingEngine(input_data_resolver("basic.json"))

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
