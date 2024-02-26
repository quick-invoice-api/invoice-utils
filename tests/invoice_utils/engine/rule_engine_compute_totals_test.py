from datetime import datetime
from decimal import Decimal

from invoice_utils.engine import InvoicingEngine
from invoice_utils.models import InvoicedItem


def test_process_computes_totals(test_basic_rules):
    engine = InvoicingEngine(test_basic_rules)

    output = engine.process(
        1, datetime.now(), [InvoicedItem("test", Decimal(2), Decimal(5))]
    )

    assert "totals" in output
    assert output["totals"]["price"] == Decimal(10)
    assert output["totals"]["total"] == Decimal(12)

    assert "taxes" in output["totals"]
    assert output["totals"]["taxes"] == [{
         "name": "vat",
         "value": Decimal("2.0")
    }]
    assert "currencies" in output["totals"]["extra"]
    assert len(output["totals"]["extra"]["currencies"]) == 1
    assert output["totals"]["extra"]["currencies"][0]["currency"] == "ABC"
    assert output["totals"]["extra"]["currencies"][0]["price"] == Decimal(11.5)
    assert output["totals"]["extra"]["currencies"][0]["total"] == Decimal("13.800000")
    assert output["totals"]["extra"]["currencies"][0]["taxes"] == [{
         "name": "vat",
         "value": Decimal("2.3")
    }]
