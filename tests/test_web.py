import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from importlib import reload
from unittest.mock import MagicMock, call, ANY, patch

import pytest
from fastapi.testclient import TestClient
from jinja2 import Environment, PackageLoader, select_autoescape

from invoice_utils.config import DEFAULT_MAIL_SUBJECT, DEFAULT_BODY_TEMPLATE_PATH

MESSAGE_ARGUMENT = 2


@pytest.fixture()
def environment(monkeypatch, request):
    if hasattr(request, "param"):
        env = request.param
    else:
        env = {}
    invoice_utils_env_vars = [
        "INVOICE_UTILS_MAIL_LOGIN_USER",
        "INVOICE_UTILS_MAIL_LOGIN_PASSWORD"
    ]
    for k in invoice_utils_env_vars:
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    from invoice_utils import config
    reload(config)
    return env


@pytest.fixture()
def http(environment, monkeypatch):
    with patch("dotenv.load_dotenv", MagicMock(name="load_dotenv")):
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
def email_invoice_request_body(invoice_request_body: dict):
    invoice_request_body["send_mail"] = True
    invoice_request_body["address"] = "test@email.com"
    return invoice_request_body


@pytest.fixture
def mock_smtp(mocker):
    result = mocker.MagicMock(name="invoice_utils.web.smtplib.SMTP")
    mocker.patch("invoice_utils.web.smtplib.SMTP", new=result)
    return result


@pytest.fixture
def server(mock_smtp):
    result = MagicMock(name="SMTPServer")
    mock_smtp.return_value.__enter__.return_value = result
    return result


def test_send_mail_param_not_provided(http, caplog, invoice_request_body):
    with caplog.at_level("INFO"):
        res = http.post("/invoice", json=invoice_request_body)

    assert "Report was sent to test@email.com" not in caplog.messages
    assert res.status_code == 201


def test_send_mail_param_fails_without_address_param(
        http, caplog, invoice_request_body: dict
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


def test_send_mail_alternate_flow(
    http, caplog, email_invoice_request_body, server
):
    with caplog.at_level("INFO"):
        res = http.post("/invoice", json=email_invoice_request_body)

    assert server.starttls.call_count == 0
    assert server.login.call_count == 0
    assert server.sendmail.call_count == 1
    assert "Report was sent to test@email.com" in caplog.messages
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
        environment, http, server, email_invoice_request_body, expected_subject,
):
    http.post("/invoice", json=email_invoice_request_body)

    assert server.sendmail.call_args_list == [
        call(ANY, ANY, ANY)
    ]
    email_content = server.sendmail.call_args.args[2]
    assert f"Subject: {expected_subject}" in email_content


@pytest.mark.parametrize(
    "environment",
    [
        {
            "INVOICE_UTILS_MAIL_LOGIN_USER": "user",
            "INVOICE_UTILS_MAIL_LOGIN_PASSWORD": "password"
        },
    ],
    indirect=["environment"]
)
def test_smtp_login_when_user_and_password_are_specified(
    environment, http, server, email_invoice_request_body,
):
    http.post("/invoice", json=email_invoice_request_body)

    assert server.login.call_args_list == [call("user", "password")]


@pytest.mark.parametrize(
    "environment",
    [
        {"INVOICE_UTILS_SMTP_TLS": True},
        {"INVOICE_UTILS_SMTP_TLS": 1},
        {"INVOICE_UTILS_SMTP_TLS": "true"},
        {"INVOICE_UTILS_SMTP_TLS": "y"},
        {"INVOICE_UTILS_SMTP_TLS": "yes"},
        {"INVOICE_UTILS_SMTP_TLS": "Yes"},
        {"INVOICE_UTILS_SMTP_TLS": "Y"},
    ],
    indirect=["environment"]
)
def test_smtp_starttls_called_when_env_flag_is_set(environment, http, server, email_invoice_request_body):
    http.post("/invoice", json=email_invoice_request_body)

    assert server.starttls.call_count == 1


@pytest.mark.parametrize(
    "environment",
    [
        {"INVOICE_UTILS_SMTP_TLS": False},
        {"INVOICE_UTILS_SMTP_TLS": 0},
        {"INVOICE_UTILS_SMTP_TLS": []},
    ],
    indirect=["environment"]
)
def test_smtp_starttls_env_flag_must_be_true_boolean(environment, http, server, email_invoice_request_body):
    http.post("/invoice", json=email_invoice_request_body)

    assert server.starttls.call_count == 0


@pytest.mark.parametrize(
    "environment",
    [
        (
            {
                "INVOICE_UTILS_MAIL_SUBJECT": "test subject",
                "INVOICE_UTILS_BODY_TEMPLATE_PATH": "test_template.html",
                "INVOICE_UTILS_SENDER_EMAIL": "test@email.com"
            }
        ),
        (
            {
                "INVOICE_UTILS_MAIL_SUBJECT": "test subject",
                "INVOICE_UTILS_BODY_TEMPLATE_PATH": DEFAULT_BODY_TEMPLATE_PATH,
                "INVOICE_UTILS_SENDER_EMAIL": "test@email.com"
            }
        )
    ],
    indirect=["environment"]
)
def test_email_body_was_sent_with_expected_body(
        environment, http, server, email_invoice_request_body
):
    http.post("/invoice", json=email_invoice_request_body)

    env = Environment(
        loader=PackageLoader('invoice_utils', 'email_templates'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template(environment.get("INVOICE_UTILS_BODY_TEMPLATE_PATH"))
    expected_body = template.render(
        sender_email=environment.get("INVOICE_UTILS_SENDER_EMAIL"),
        invoice_id=email_invoice_request_body["header"]["number"],
        sender_name=email_invoice_request_body["seller"]["name"]
    )

    assert server.sendmail.call_args_list == [
        call(ANY, ANY, ANY)
    ]
    email_content = server.sendmail.call_args.args[MESSAGE_ARGUMENT]
    assert expected_body in email_content


@pytest.mark.parametrize(
    "environment",
    [
        (
            {
                "INVOICE_UTILS_MAIL_SUBJECT": "test subject",
                "INVOICE_UTILS_BODY_TEMPLATE_PATH": "test_template.html",
                "INVOICE_UTILS_SENDER_EMAIL": "test@email.com"
            }
        )
    ],
    indirect=["environment"]
)
def test_sendmail_was_called_with_pdf_attachment(environment, http, server, email_invoice_request_body):
    http.post("/invoice", json=email_invoice_request_body)
    timestamp = datetime.fromisoformat(email_invoice_request_body['header']['timestamp'])
    invoice_number = int(email_invoice_request_body['header']['number'])
    invoice_name = f"{timestamp:%Y%m%d}-{invoice_number:04}-invoice.pdf"

    assert server.sendmail.call_args_list == [
        call(ANY, ANY, ANY)
    ]
    email_content = server.sendmail.call_args.args[MESSAGE_ARGUMENT]
    assert f"Content-Disposition: attachment; filename=\"{invoice_name}\"" in email_content
