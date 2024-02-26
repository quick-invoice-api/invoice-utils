import os.path
import smtplib
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from os.path import basename

from dotenv import load_dotenv
from logging import basicConfig, getLogger, DEBUG
from pathlib import Path
from sys import stdout
from typing import Optional
from email.mime.text import MIMEText

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from jinja2 import Environment, PackageLoader, select_autoescape

from invoice_utils.api import template_router, templates_router
from invoice_utils.engine import InvoicingEngine
from invoice_utils.models import InvoicedItem
load_dotenv()  # Need to do this now for it to work.
import invoice_utils.config as config
from invoice_utils.render import PdfInvoiceRenderer


# basic setup
basicConfig(stream=stdout, level=DEBUG)
log = getLogger("invoice-utils")

# API setup
API_PATH_PREFIX = "/api/v1"
app = FastAPI()
app.include_router(template_router, prefix=API_PATH_PREFIX)
app.include_router(templates_router, prefix=API_PATH_PREFIX)


class InvoiceRequestHeader(BaseModel):
    number: str
    timestamp: datetime
    items: list


class InvoiceEntityBank(BaseModel):
    iban: str
    name: str


class InvoiceTaxInfo(BaseModel):
    id: str
    registration_number: Optional[str] = None


class InvoiceEntity(BaseModel):
    name: str
    address: str
    bank: Optional[InvoiceEntityBank] = None
    tax_info: InvoiceTaxInfo
    admin_location: Optional[str] = None


class InvoiceRequest(BaseModel):
    header: InvoiceRequestHeader
    send_mail: bool = False
    address: str = None
    buyer: InvoiceEntity
    seller: InvoiceEntity
    items: list[InvoicedItem]


class InvoiceRequestInputError(Exception):
    def __init__(self, message: str):
        self.message = message


class InvoiceRequestEmailError(Exception):
    def __init__(self, message: str):
        self.message = message


@app.exception_handler(InvoiceRequestInputError)
def input_error_handler(request: InvoiceRequest, exc: InvoiceRequestInputError):
    return JSONResponse(
        status_code=422,
        content={"message": f"{exc.message}"},
    )


@app.exception_handler(InvoiceRequestEmailError)
def email_error_handler(request: InvoiceRequest, exc: InvoiceRequestEmailError):
    return JSONResponse(status_code=502, content={"message": f"{exc.message}"})


@app.post("/invoice", status_code=201)
def generate_invoice(request: InvoiceRequest):
    root_dir = Path(__file__).parent
    basic_rules = str(root_dir / "basic.json")
    engine = InvoicingEngine()
    context = engine.process(
        int(request.header.number), request.header.timestamp, request.items
    )
    invoice_content, invoice_path = _render_invoice(context, request, root_dir)
    _send_mail(request, invoice_content, invoice_path)
    return context


def _render_invoice(context, request, root_dir):
    renderer = PdfInvoiceRenderer("invoice")
    invoice_name = f"{request.header.timestamp:%Y%m%d}-{int(request.header.number):04}-invoice.pdf"
    invoice_path = root_dir / config.INVOICE_UTILS_INVOICE_DIR / invoice_name
    if not os.path.isdir(root_dir / config.INVOICE_UTILS_INVOICE_DIR):
        raise HTTPException(status_code=507, detail="No local storage available for invoices")
    if not os.access(root_dir / config.INVOICE_UTILS_INVOICE_DIR, os.W_OK):
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
