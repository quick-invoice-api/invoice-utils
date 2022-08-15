import pathlib
from datetime import datetime, tzinfo

import pytest

from invoice_utils import InvoicingEngine


@pytest.fixture(scope="session")
def input_data_resolver():
    def f(name: str) -> str:
        data_dir = pathlib.Path(__file__).parent.parent/"data"
        desired_path = data_dir/name
        if desired_path.exists():
            return str(desired_path.absolute())
        raise FileNotFoundError(f"file {name} not found in the project's data dir")
    return f


@pytest.fixture(scope="function")
def basic_invoice_engine(input_data_resolver):
    return InvoicingEngine(input_data_resolver("basic.json"))


def test_process_empty_input_data_outputs_base_invoice_document_structure(basic_invoice_engine):
    expected_invoice_no = 1
    expected_invoice_date = datetime(2022, 1, 15, 13, 14, 15)

    output = basic_invoice_engine.process(expected_invoice_no, expected_invoice_date)

    assert output == {
        "header": {
            "number": expected_invoice_no,
            "date": expected_invoice_date,
            "customer": {},
            "emitter": {}
        },
        "details": [],
        "totals": {
            "price": 0,
            "total": 0,
            "extra": {}
        }
    }
