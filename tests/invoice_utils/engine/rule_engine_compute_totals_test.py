from datetime import datetime
from decimal import Decimal

from invoice_utils.engine import InvoicingEngine
from invoice_utils.models import InvoicedItem


def test_process_computes_totals(input_data_resolver):
    engine = InvoicingEngine(input_data_resolver("basic.json"))

    output = engine.process(
        1, datetime.now(), [InvoicedItem("test", Decimal(2), Decimal(5))]
    )

    assert "totals" in output
    assert output["totals"]["price"] == Decimal(10)
    assert output["totals"]["total"] == Decimal(12)

    assert "taxes" in output["totals"]
    assert output["totals"]["taxes"] == [{
         "name": "vat",
         "value": Decimal("2.000000")
    }]
