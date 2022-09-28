import pytest

from invoice_utils import InvoicingEngine
from invoice_utils._engine import InvoicingInputError


def test_invoicing_engine_with_empty_file():
    engine = InvoicingEngine("tests/data/basic.json")
    assert engine is not None


@pytest.mark.parametrize("file_name", [None, "", "does-not-exist.txt"])
def test_invoicing_engine_raises_input_error_if_file_not_found(file_name):
    with pytest.raises(InvoicingInputError) as ve:
        InvoicingEngine(file_name)

    assert str(ve.value) == f"file '{file_name}' not found"


def test_invoicing_engine_raises_input_format_error_if_file_content_is_not_valid_json():
    with pytest.raises(InvoicingInputError) as ve:
        InvoicingEngine("tests/data/invalid-format-file.text")

    assert (
        str(ve.value)
        == "file 'invalid-format-file.text' not does not contain valid json"
    )
