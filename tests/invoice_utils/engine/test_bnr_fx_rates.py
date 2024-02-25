from datetime import datetime
from decimal import Decimal

import pytest

from invoice_utils.engine import InvoicingEngine
from invoice_utils.models import InvoicedItem


@pytest.fixture
def invoiced_item():
    return InvoicedItem(
        text="sample invoiced item",
        quantity=Decimal("1.0"),
        unit_price=Decimal("100.0")
    )


@pytest.fixture
def invoice_date():
    return datetime(2011, 11, 11)


@pytest.fixture
def bnr_sample_path(data_dir):
    return str(data_dir / "bnr-sample.json")


@pytest.fixture
def engine(bnr_sample_path, data_dir, request):
    file_path = (
        bnr_sample_path
        if not hasattr(request, "param") or request.param is None
        else str(data_dir / request.param)
    )
    return InvoicingEngine(file_path)


def test_engine_calls_bnr_for_invoice_date(
    engine, invoice_date, invoiced_item, responses, read_text
):
    bnr_resp = responses.get(
        "https://bnr.ro/files/xml/years/nbrfxrates2011.xml",
        content_type="text/xml",
        body=read_text("bnr-response-1-item.xml")
    )
    engine.process(12, invoice_date, [invoiced_item])

    assert bnr_resp.call_count == 1
    assert bnr_resp.status == 200


@pytest.mark.parametrize("engine", ["empty.json"], indirect=["engine"])
def test_engine_does_not_call_bnr(
    engine, invoice_date, invoiced_item, responses, read_text
):
    engine.process(12, invoice_date, [invoiced_item])

    assert responses.assert_call_count(
        "https://bnr.ro/files/xml/years/nbrfxrates2011.xml", 0
    ) is True
