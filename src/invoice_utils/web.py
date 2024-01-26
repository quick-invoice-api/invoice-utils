import smtplib
from datetime import datetime
from logging import basicConfig, getLogger, DEBUG
from pathlib import Path
from sys import stdout
from typing import Optional
from email.mime.text import MIMEText

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from invoice_utils.engine import InvoicingEngine
from invoice_utils.models import InvoicedItem
import invoice_utils.config as config

app = FastAPI()
basicConfig(stream=stdout, level=DEBUG)
log = getLogger("invoice-utils")


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
    engine = InvoicingEngine(basic_rules)
    _send_mail(request)
    return engine.process(
        int(request.header.number), request.header.timestamp, request.items
    )


def _send_mail(request):
    if not request.send_mail:
        return
    if not request.address:
        raise InvoiceRequestInputError(
            "Address was not provided but send_mail is set to True."
        )
    message = _create_message(request)
    try:
        with smtplib.SMTP(config.INVOICE_UTILS_MAIL_HOST, config.INVOICE_UTILS_MAIL_PORT) as server:
            server.sendmail(config.INVOICE_UTILS_SENDER_EMAIL, request.address, message.as_string())
        log.info("Report was sent to %s", request.address)
    except Exception as e:
        raise InvoiceRequestEmailError("There was a problem sending the email.") from e


def _create_message(request):
    message = MIMEText("Empty Body", "html")
    message["From"] = config.INVOICE_UTILS_SENDER_EMAIL
    message["To"] = request.address
    message["Subject"] = config.INVOICE_UTILS_MAIL_SUBJECT
    return message
