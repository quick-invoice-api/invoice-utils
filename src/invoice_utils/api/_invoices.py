import os.path
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from http import HTTPStatus
from os.path import basename

from logging import getLogger
from pathlib import Path
from email.mime.text import MIMEText

from fastapi import HTTPException, Depends, APIRouter
from jinja2 import Environment, PackageLoader, select_autoescape

from invoice_utils.api._errors import InvoiceRequestInputError, InvoiceRequestEmailError
from invoice_utils.api._request import InvoiceRequest
from invoice_utils.dal import Repository, Template
import invoice_utils.depends as di
from invoice_utils.engine import InvoicingEngine

import invoice_utils.config as config
from invoice_utils.render import PdfInvoiceRenderer


log = getLogger(__name__)
router = APIRouter(prefix="/invoices")


@router.post("/", status_code=201)
def generate_invoice(request: InvoiceRequest, repo: Repository[str, Template] = Depends(di.template_repo)):
    found, rule_template = repo.get_by_key(config.INVOICE_UTILS_RULE_TEMPLATE_NAME)
    if request.rule_template_name:
        found, rule_template = repo.get_by_key(request.rule_template_name)
    if not found:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Rule Template does not exist.")
    rules = rule_template.rules
    engine = InvoicingEngine(rules)
    context = engine.process(
        int(request.header.number), request.header.timestamp, request.items
    )
    invoice_content, invoice_path = _render_invoice(context, request)
    _send_mail(request, invoice_content, invoice_path)
    return context


def _render_invoice(context, request):
    invoices_dir = Path(config.INVOICE_UTILS_INVOICE_DIR).absolute()
    renderer = PdfInvoiceRenderer("invoice")
    invoice_name = f"{request.header.timestamp:%Y%m%d}-{int(request.header.number):04}-invoice.pdf"
    invoice_path = invoices_dir / invoice_name
    if not os.path.isdir(invoices_dir):
        raise HTTPException(status_code=507, detail="No local storage available for invoices")
    if not os.access(invoices_dir, os.W_OK):
        raise HTTPException(status_code=507, detail="Insufficient rights to store invoice")
    invoice_content = renderer.render(context, str(invoice_path))
    return invoice_content, invoice_path


def _send_mail(request, invoice_content, invoice_path):
    if not request.send_mail:
        return
    if not request.address:
        raise InvoiceRequestInputError(
            "Address was not provided but send_mail is set to True."
        )
    message = _create_message(request, invoice_content, invoice_path)
    try:
        with smtplib.SMTP(config.INVOICE_UTILS_MAIL_HOST, config.INVOICE_UTILS_MAIL_PORT) as server:
            if config.INVOICE_UTILS_SMTP_TLS:
                server.starttls()
            if config.INVOICE_UTILS_MAIL_LOGIN_USER is not None and config.INVOICE_UTILS_MAIL_LOGIN_PASSWORD is not None:
                server.login(config.INVOICE_UTILS_MAIL_LOGIN_USER, config.INVOICE_UTILS_MAIL_LOGIN_PASSWORD)
            server.sendmail(config.INVOICE_UTILS_SENDER_EMAIL, request.address, message.as_string())
        log.info("Report was sent to %s", request.address)
    except Exception as e:
        raise InvoiceRequestEmailError("There was a problem sending the email.") from e


def _create_message(request, invoice_content, invoice_path):
    html_body = _render_body_template(request)
    message = MIMEMultipart()
    part = MIMEText(html_body, "html")
    message.attach(part)
    message["From"] = config.INVOICE_UTILS_SENDER_EMAIL
    message["To"] = request.address
    message["Subject"] = config.INVOICE_UTILS_MAIL_SUBJECT
    file_part = MIMEApplication(
        invoice_content,
        Name=basename(invoice_path)
    )
    file_part['Content-Disposition'] = 'attachment; filename="%s"' % basename(invoice_path)
    message.attach(file_part)
    return message


def _render_body_template(request):
    env = Environment(
        loader=PackageLoader(config.INVOICE_UTILS_BODY_TEMPLATE_PACKAGE, config.INVOICE_UTILS_TEMPLATES_DIR),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template(config.INVOICE_UTILS_BODY_TEMPLATE_NAME)
    html_body = template.render(
        sender_email=config.INVOICE_UTILS_SENDER_EMAIL,
        invoice_id=request.header.number,
        sender_name=request.seller.name
    )
    return html_body
