import pytest
from fastapi.testclient import TestClient
import invoice_utils.web as web


@pytest.fixture()
def http():
    return TestClient(web.app)


@pytest.fixture()
def invoice_request_body():
    return {
        "header": {"number": "1", "timestamp": "2023-11-14T09:00:00+00:00", "items": []},
        "buyer": {"name": "a", "address": "b", "tax_info": {"id": "c"}},
        "seller": {"name": "a", "address": "b", "tax_info": {"id": "c"}},
        "items": [{"text": "Some t", "quantity": "2", "unit_price": "45"}]
    }


def test_send_mail_param(http, caplog, invoice_request_body):
    with caplog.at_level("INFO"):
        res = http.post("/invoice", json=invoice_request_body)

    assert "I've sent the mail like you asked." not in caplog.messages
    assert res.status_code == 201


def test_send_mail_param_is_true(http, caplog, invoice_request_body):
    invoice_request_body["send_mail"] = True
    with caplog.at_level("INFO"):
        res = http.post("/invoice", json=invoice_request_body)

    assert "I've sent the mail like you asked." in caplog.messages
    assert res.status_code == 201
