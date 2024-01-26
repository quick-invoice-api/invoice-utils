import os
import re
import smtplib
from email.mime.text import MIMEText
from importlib import reload
from unittest.mock import MagicMock, call, ANY

import pytest
from fastapi.testclient import TestClient

from invoice_utils.config import DEFAULT_MAIL_SUBJECT

MESSAGE_ARGUMENT = 2


@pytest.fixture()
def environment(monkeypatch, request):
    if hasattr(request, "param"):
        env = request.param
    else:
        env = {}
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    from invoice_utils import config
    reload(config)
    return env


@pytest.fixture()
def http(environment):
    import invoice_utils.web as web
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


@pytest.fixture
def email_invoice_request_body(invoice_request_body):
    invoice_request_body["send_mail"] = True
    invoice_request_body["address"] = "test@email.com"
    return invoice_request_body


@pytest.fixture
def mock_smtp(mocker):
    result = mocker.MagicMock(name="invoice_utils.web.smtplib.SMTP")
    mocker.patch("invoice_utils.web.smtplib.SMTP", new=result)
    return result


@pytest.fixture
def sendmail(mock_smtp):
    result = MagicMock(name="sendmail")
    mock_smtp.return_value.__enter__.return_value.sendmail = result
    return result


@pytest.fixture()
def email_body():
    body = "test body"
    message = MIMEText(body, "html")
    # message["From"] = INVOICE_UTILS_SENDER_EMAIL
    # message["To"] = "test@email.com"
    # message["Subject"] = INVOICE_UTILS_MAIL_SUBJECT
    return message.as_string()


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
    http, caplog, email_invoice_request_body, mock_smtp
):
    with caplog.at_level("INFO"):
        res = http.post("/invoice", json=email_invoice_request_body)

    assert "Report was sent to test@email.com" in caplog.messages
    # Because it's used as a context manager.
    assert mock_smtp.return_value.__enter__.return_value.sendmail.call_count == 1
    assert res.status_code == 201


def test_send_mail_fails_for_smtp_exception(http, caplog, email_invoice_request_body, mock_smtp):
    mock_smtp.side_effect = smtplib.SMTPException

    with caplog.at_level("INFO"):
        res = http.post("/invoice", json=email_invoice_request_body)

    assert "Report was sent to test@email.com" not in caplog.messages
    assert res.json()["message"] == "There was a problem sending the email."
    assert res.status_code == 502


@pytest.mark.parametrize(
    "environment,expected_subject",
    [
        ({"INVOICE_UTILS_MAIL_SUBJECT": "test subject"}, "test subject"),
        ({}, DEFAULT_MAIL_SUBJECT),
    ],
    indirect=["environment"]
)
def test_email_sent_with_expected_subject(
    environment, http, sendmail, email_invoice_request_body, expected_subject,
):
    http.post("/invoice", json=email_invoice_request_body)

    assert sendmail.call_args_list == [
        call(ANY, ANY, ANY)
    ]
    email_content = sendmail.call_args.args[2]
    assert f"Subject: {expected_subject}" in email_content
