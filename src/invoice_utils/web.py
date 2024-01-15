from datetime import datetime
from logging import basicConfig, getLogger, INFO, DEBUG
from pathlib import Path
from sys import stdout
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from invoice_utils.engine import InvoicingEngine
from invoice_utils.models import InvoicedItem

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


class InvoicingRequestInputError(Exception):
    def __init__(self, message: str):
        self.message = message


@app.exception_handler(InvoicingRequestInputError)
def input_error_handler(request: InvoiceRequest, exc: InvoicingRequestInputError):
    return JSONResponse(
        status_code=422,
        content={"message": f"{exc.message}"},
    )


@app.post("/invoice", status_code=201)
def generate_invoice(request: InvoiceRequest):
    root_dir = Path(__file__).parent
    basic_rules = str(root_dir / "basic.json")
    engine = InvoicingEngine(basic_rules)
    if request.send_mail:
        if not request.address:
            raise InvoicingRequestInputError("Address was not provided but send_mail is set to True.")
        log.info("Report was sent to {}".format(request.address))
    return engine.process(int(request.header.number), request.header.timestamp, request.items)
