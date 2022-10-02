from datetime import datetime
from decimal import Decimal
from pathlib import Path

from invoice_utils.engine import InvoicingEngine
from invoice_utils.models import InvoicedItem
from invoice_utils.render import PdfInvoiceRenderer

root_dir = Path(__file__).parent
investigo_rules = str(root_dir / "basic.json")
invoiced_items = [
    (1, datetime(2022, 10, 2),
     [InvoicedItem(
         text="Rendered services according to contract no. 1 from 2016",
         quantity=Decimal("4"),
         unit_price=Decimal("25.0")
     )]),
]
engine = InvoicingEngine(str(investigo_rules))

for invoice in invoiced_items:
    context = engine.process(*invoice)
    renderer = PdfInvoiceRenderer("invoice")
    out_path = root_dir / f"{invoice[1]:%Y%m%d}-{invoice[0]:04}-invoice.pdf"
    renderer.render(context, str(out_path))
