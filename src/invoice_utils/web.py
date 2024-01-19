import smtplib
from datetime import datetime
from logging import basicConfig, getLogger, INFO, DEBUG
from pathlib import Path
from sys import stdout
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from invoice_utils.engine import InvoicingEngine
from invoice_utils.models import InvoicedItem
from invoice_utils.config import (
    INVOICE_UTILS_MAIL_HOST,
    INVOICE_UTILS_MAIL_PORT,
    INVOICE_UTILS_MAIL_LOGIN_PASSWORD,
    INVOICE_UTILS_MAIL_LOGIN_USER,
    INVOICE_UTILS_SENDER_EMAIL,
    INVOICE_UTILS_MAIL_SUBJECT,
)

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
    if request.send_mail:
        if not request.address:
            raise InvoiceRequestInputError(
                "Address was not provided but send_mail is set to True."
            )
        message = MIMEText("Empty Body", "html")
        message["From"] = INVOICE_UTILS_SENDER_EMAIL
        message["To"] = request.address
        message["Subject"] = INVOICE_UTILS_MAIL_SUBJECT
        try:
            with smtplib.SMTP(INVOICE_UTILS_MAIL_HOST, INVOICE_UTILS_MAIL_PORT) as server:
                server.starttls()
                server.login(INVOICE_UTILS_MAIL_LOGIN_USER, INVOICE_UTILS_MAIL_LOGIN_PASSWORD)
                server.sendmail(INVOICE_UTILS_SENDER_EMAIL, request.address, message.as_string())
        except Exception as e:
            log.debug(e)
            raise InvoiceRequestEmailError("There was a problem sending the email.")

        log.info("Report was sent to {}".format(request.address))
    return engine.process(
        int(request.header.number), request.header.timestamp, request.items
    )
