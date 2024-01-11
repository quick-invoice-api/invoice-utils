import pytest
from fastapi.testclient import TestClient
import invoice_utils.web as web


@pytest.fixture()
def http():
    return TestClient(web.app)


def test_send_mail_param(http):
    res = http.post("/invoice", json={"header": {"number": "1", "timestamp": "2023-11-14T09:00:00+00:00", "items": []},
                                "buyer": {"name": "a", "address": "b", "tax_info": {"id": "c"}},
                                "seller": {"name": "a", "address": "b", "tax_info": {"id": "c"}},
                                "items": [{"text": "Some t", "quantity": "2", "unit_price": "45"}]})

    assert res.status_code == 201
