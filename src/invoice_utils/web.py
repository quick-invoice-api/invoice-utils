from datetime import datetime
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI()


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
    buyer: InvoiceEntity
    seller: InvoiceEntity


@app.post("/invoice")
def generate_invoice(request: InvoiceRequest):
    return {}
