import smtplib
import pytest
from fastapi.testclient import TestClient
import invoice_utils.web as web


@pytest.fixture()
def http():
    return TestClient(web.app)


@pytest.fixture()
def invoice_request_body():
    return {
        "header": {
            "number": "1",
            "timestamp": "2023-11-14T09:00:00+00:00",
            "items": [],
        },
        "buyer": {"name": "a", "address": "b", "tax_info": {"id": "c"}},
        "seller": {"name": "a", "address": "b", "tax_info": {"id": "c"}},
        "items": [{"text": "Some t", "quantity": "2", "unit_price": "45"}],
    }


def test_send_mail_param_not_provided(http, caplog, invoice_request_body):
    with caplog.at_level("INFO"):
        res = http.post("/invoice", json=invoice_request_body)

    assert "Report was sent to test@email.com" not in caplog.messages
    assert res.status_code == 201


def test_send_mail_param_fails_without_address_param(
    http, caplog, invoice_request_body
):
    invoice_request_body["send_mail"] = True
    with caplog.at_level("INFO"):
        res = http.post("/invoice", json=invoice_request_body)

    assert "Report was sent to " not in caplog.messages
    assert (
        res.json()["message"]
        == "Address was not provided but send_mail is set to True."
    )
    assert res.status_code == 422


def test_send_mail_param_is_true_and_address_provided(
    http, caplog, invoice_request_body, mocker
):
    invoice_request_body["send_mail"] = True
    invoice_request_body["address"] = "test@email.com"

    mock_smtp = mocker.MagicMock(name="invoice_utils.web.smtplib.SMTP")
    mocker.patch("invoice_utils.web.smtplib.SMTP", new=mock_smtp)

    with caplog.at_level("INFO"):
        res = http.post("/invoice", json=invoice_request_body)

    assert "Report was sent to test@email.com" in caplog.messages
    # Because it's used as a context manager.
    assert mock_smtp.return_value.__enter__.return_value.sendmail.call_count == 1
    assert res.status_code == 201


def test_send_mail_fails_for_smtp_exception(http, caplog, invoice_request_body, mocker):
    invoice_request_body["send_mail"] = True
    invoice_request_body["address"] = "test@email.com"

    mock_smtp = mocker.MagicMock(name="invoice_utils.web.smtplib.SMTP")
    mocker.patch("invoice_utils.web.smtplib.SMTP", new=mock_smtp)

    mock_smtp.side_effect = smtplib.SMTPException

    with caplog.at_level("INFO"):
        res = http.post("/invoice", json=invoice_request_body)

    assert "Report was sent to test@email.com" not in caplog.messages
    assert res.json()["message"] == "There was a problem sending the email."
    assert res.status_code == 502
