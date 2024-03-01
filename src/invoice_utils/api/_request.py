from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from starlette.requests import Request

from invoice_utils.dal import Template
from invoice_utils.models import InvoicedItem


class TemplateRequestBody(BaseModel):
    name: str
    rules: list[dict]

    def to_model(self) -> Template:
        return Template(name=self.name, rules=self.rules)


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


class InvoiceRequestHeader(BaseModel):
    number: str
    timestamp: datetime
    items: list


class InvoiceRequest(BaseModel):
    header: InvoiceRequestHeader
    send_mail: bool = False
    address: str = None
    rule_template_name: str = None
    buyer: InvoiceEntity
    seller: InvoiceEntity
    items: list[InvoicedItem]
