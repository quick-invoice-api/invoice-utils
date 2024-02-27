import smtplib
from unittest.mock import MagicMock, call, ANY, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from jinja2 import TemplateNotFound

from invoice_utils.config import DEFAULT_MAIL_SUBJECT, DEFAULT_BODY_TEMPLATE_NAME, DEFAULT_BODY_TEMPLATE_PACKAGE, \
    DEFAULT_BODY_TEMPLATE_DIRECTORY, DEFAULT_INVOICE_DIR

MESSAGE_ARGUMENT = 2


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


@pytest.fixture
def expected_body():
    return "<p>Hello,</p>\n<p>This is a test email from test@email.com.</p>\n<p>Testing invoice with id 1 issued by " \
           "a.</p>\n<p>Please don\'t contact us</p>\n<p>~a</p>"


@pytest.fixture
def mock_render(mocker):
    result = MagicMock(name="invoice_utils.web.PdfInvoiceRenderer.render")
    mocker.patch("invoice_utils.web.PdfInvoiceRenderer.render", new=result)
    result.return_value = b"test pdf content"
    return result


def test_send_mail_param_not_provided(http, caplog, mock_render, invoice_request_body):
    with caplog.at_level("INFO"):
        res = http.post("/invoice", json=invoice_request_body)

    assert "Report was sent to test@email.com" not in caplog.messages
    assert res.status_code == 201


def test_send_mail_param_fails_without_address_param(
    http, caplog, mock_render, invoice_request_body: dict
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
    http, caplog, mock_render, email_invoice_request_body, server
):
    with caplog.at_level("INFO"):
        res = http.post("/invoice", json=email_invoice_request_body)

    assert server.starttls.call_count == 0
    assert server.login.call_count == 0
    assert server.sendmail.call_count == 1
    assert "Report was sent to test@email.com" in caplog.messages
    assert res.status_code == 201


def test_send_mail_fails_for_smtp_exception(http, caplog, mock_render, email_invoice_request_body, mock_smtp):
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
    environment, http, server, mock_render, email_invoice_request_body, expected_subject,
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
    environment, http, server, mock_render, email_invoice_request_body,
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
def test_smtp_starttls_called_when_env_flag_is_set(
    environment, http, server, mock_render, email_invoice_request_body
):
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
def test_smtp_starttls_env_flag_must_be_true_boolean(
    environment, http, server, mock_render, email_invoice_request_body
):
    http.post("/invoice", json=email_invoice_request_body)

    assert server.starttls.call_count == 0


@pytest.mark.parametrize(
    "environment",
    [
        (
            {
                "INVOICE_UTILS_MAIL_SUBJECT": "test subject",
                "INVOICE_UTILS_SENDER_EMAIL": "test@email.com",
                "INVOICE_UTILS_BODY_TEMPLATE_NAME": "test_template.html",
                "INVOICE_UTILS_BODY_TEMPLATE_PACKAGE": "tests",
                "INVOICE_UTILS_TEMPLATES_DIR": "data"
            }
        )
    ],
    indirect=["environment"]
)
def test_email_body_was_sent_with_expected_body(
    environment, http, server, mock_render, email_invoice_request_body, expected_body
):
    http.post("/invoice", json=email_invoice_request_body)

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
def test_sendmail_was_called_with_pdf_attachment(
    environment, http, server, mock_render, email_invoice_request_body
):
    http.post("/invoice", json=email_invoice_request_body)

    email_content = server.sendmail.call_args.args[MESSAGE_ARGUMENT]
    assert "Content-Disposition: attachment; filename=\"20231114-0001-invoice.pdf\"" in email_content


@pytest.mark.parametrize(
    "environment",
    [
        (
            {
                "INVOICE_UTILS_MAIL_SUBJECT": "test subject",
                "INVOICE_UTILS_BODY_TEMPLATE_PATH": "test_template.html",
                "INVOICE_UTILS_SENDER_EMAIL": "test@email.com",
                "INVOICE_UTILS_INVOICE_DIR": DEFAULT_INVOICE_DIR
            }
        )
    ],
    indirect=["environment"]
)
def test_invoice_generated_within_specified_dir(
    environment, http, server, mock_render, email_invoice_request_body
):
    http.post("/invoice", json=email_invoice_request_body)

    assert environment.get("INVOICE_UTILS_INVOICE_DIR") in mock_render.call_args.args[1]


@pytest.mark.parametrize(
    "environment",
    [
        (
            {
                "INVOICE_UTILS_MAIL_SUBJECT": "test subject",
                "INVOICE_UTILS_BODY_TEMPLATE_PATH": "test_template.html",
                "INVOICE_UTILS_SENDER_EMAIL": "test@email.com",
                "INVOICE_UTILS_INVOICE_DIR": "bad_directory"
            }
        )
    ],
    indirect=["environment"]
)
def test_invoice_generation_fails_if_directory_does_not_exist(
    environment, http, server, mock_render, email_invoice_request_body
):
    res = http.post("/invoice", json=email_invoice_request_body)
    assert res.status_code == 507
    assert res.json() == {"detail": "No local storage available for invoices"}


@pytest.mark.parametrize(
    "environment",
    [
        (
            {
                "INVOICE_UTILS_MAIL_SUBJECT": "test subject",
                "INVOICE_UTILS_BODY_TEMPLATE_PATH": "test_template.html",
                "INVOICE_UTILS_SENDER_EMAIL": "test@email.com",
                "INVOICE_UTILS_INVOICE_DIR": "bad_directory"
            }
        )
    ],
    indirect=["environment"]
)
def test_invoice_generation_fails_if_directory_does_not_exist(
    environment, http, server, mocker, email_invoice_request_body
):
    with mocker.patch("invoice_utils.web.os.path.isdir", return_value=True):
        with mocker.patch("invoice_utils.web.os.access", return_value=False):
            res = http.post("/invoice", json=email_invoice_request_body)
    assert res.status_code == 507
    assert res.json() == {"detail": "Insufficient rights to store invoice"}


def test_render_body_is_called_with_default_values(
    http, server, mock_render, email_invoice_request_body, mocker
):
    mock_env = mocker.MagicMock(name="invoice_utils.web.Environment")
    mocker.patch("invoice_utils.web.Environment", new=mock_env)

    http.post("/invoice", json=email_invoice_request_body)

    assert mock_env.call_args.kwargs["loader"].package_name == DEFAULT_BODY_TEMPLATE_PACKAGE
    assert mock_env.call_args.kwargs["loader"].package_path == DEFAULT_BODY_TEMPLATE_DIRECTORY
    assert DEFAULT_BODY_TEMPLATE_NAME in mock_env.return_value.get_template.call_args.args


@pytest.mark.parametrize(
    "environment, expected_error",
    [
        ({"INVOICE_UTILS_BODY_TEMPLATE_NAME": "bad_template.html"}, TemplateNotFound),
        ({"INVOICE_UTILS_BODY_TEMPLATE_PACKAGE": "bad_package"}, ModuleNotFoundError),
        ({"INVOICE_UTILS_TEMPLATES_DIR": "bad_dir"}, ValueError)
    ],
    indirect=["environment"]
)
def test_template_related_variables_with_bad_inputs_raise_errors(
    environment, http, server, mock_render, email_invoice_request_body, expected_error
):
    with pytest.raises(expected_error):
        http.post("/invoice", json=email_invoice_request_body)


@pytest.mark.parametrize(
    "environment",
    [
        ({"INVOICE_UTILS_INVOICE_DIR": "bad_directory"}),
        ({"INVOICE_UTILS_RULE_TEMPLATE_NAME": "bad_name.json"})
    ],
    indirect=["environment"]
)
def test_app_does_not_start_with_bad_default_rule_template(
    environment, monkeypatch, template_repo, email_invoice_request_body
):
    with patch("dotenv.load_dotenv", MagicMock(name="load_dotenv")):
        import invoice_utils.web as web

        with pytest.raises(HTTPException) as exc_info:
            with TestClient(web.app) as client:
                client.post("/invoice", json=email_invoice_request_body)
        assert exc_info.value.status_code == 500
        assert "does not exist" in exc_info.value.detail
