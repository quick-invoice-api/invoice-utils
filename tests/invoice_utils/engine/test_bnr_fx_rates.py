from datetime import datetime
from decimal import Decimal

import pytest

from invoice_utils.engine import InvoicingEngine
from invoice_utils.models import InvoicedItem


TEST_INVOICE_NUMBER = 11
TEST_INVOICE_DATE = datetime(2011, 11, 11)


@pytest.fixture
def invoiced_item():
    return InvoicedItem(
        text="sample invoiced item",
        quantity=Decimal("1.0"),
        unit_price=Decimal("100.0")
    )


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


@pytest.fixture
def bnr_res(responses, read_text, request):
    file_name = (
        "bnr-response-1-item.xml"
        if not hasattr(request, "param") or request.param is None
        else request.param
    )
    return responses.get(
        f"https://bnr.ro/files/xml/years/nbrfxrates{TEST_INVOICE_DATE.year}.xml",
        content_type="text/xml",
        body=read_text(file_name)
    )


def test_engine_calls_bnr_for_invoice_date(engine, invoiced_item, bnr_res):
    engine.process(TEST_INVOICE_NUMBER, TEST_INVOICE_DATE, [invoiced_item])

    assert bnr_res.call_count == 1
    assert bnr_res.status == 200


@pytest.mark.parametrize("engine", ["empty.json"], indirect=["engine"])
def test_engine_does_not_call_bnr(engine, invoiced_item, responses):
    engine.process(TEST_INVOICE_NUMBER, TEST_INVOICE_DATE, [invoiced_item])

    assert responses.assert_call_count(
        "https://bnr.ro/files/xml/years/nbrfxrates2011.xml", 0
    ) is True


def test_engine_with_bnr_rule_makes_ron_the_main_currency(engine, invoiced_item, bnr_res):
    result = engine.process(
        TEST_INVOICE_NUMBER, TEST_INVOICE_DATE, [invoiced_item]
    )

    assert result["header"]["currency"]["main"] == "RON"


@pytest.mark.parametrize(
    "engine", ["bnr-sample-no-symbols.json", "bnr-sample-missing-symbols.json"], indirect=["engine"]
)
def test_engine_bnr_rule_no_symbols_no_exchange_rates(engine, invoiced_item, bnr_res):
    result = engine.process(
        TEST_INVOICE_NUMBER, TEST_INVOICE_DATE, [invoiced_item]
    )

    assert result["header"]["currency"]["main"] == "RON"
    assert result["header"]["currency"]["exchangeRates"] == {}


def test_engine_bnr_rule_adds_exchange_rates_for_symbols(engine, invoiced_item, bnr_res):
    result = engine.process(
        TEST_INVOICE_NUMBER, TEST_INVOICE_DATE, [invoiced_item]
    )

    assert len(result["header"]["currency"]["exchangeRates"]) == 2
    rates = result["header"]["currency"]["exchangeRates"]
    assert rates["EUR"] == Decimal("4.9273")
    assert rates["USD"] == Decimal("4.6766")


@pytest.mark.parametrize("bnr_res", ["bnr-response-invalid.xml"], indirect=["bnr_res"])
def test_engine_bnr_rule_invalid_xml_response_logs_warning(
    engine, invoiced_item, bnr_res, caplog
):
    with caplog.at_level("WARNING"):
        result = engine.process(
            TEST_INVOICE_NUMBER, TEST_INVOICE_DATE, [invoiced_item]
        )

    assert result["header"]["currency"]["exchangeRates"] == {}
    assert caplog.messages[0] == "invalid XML downloaded from BNR"
