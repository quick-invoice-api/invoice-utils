from datetime import datetime
from decimal import Decimal
from pathlib import Path

from invoice_utils.models import InvoicedItem
from invoice_utils.engine import InvoicingEngine
from invoice_utils.render import PdfInvoiceRenderer

root_dir = Path(__file__).parent
basic_rules = str(root_dir / "basic.json")
out_path = str(root_dir / "out.pdf")

engine = InvoicingEngine(str(basic_rules))
context = engine.process(1, datetime.now(), [
    InvoicedItem("invoiced item #1", Decimal(20), Decimal(15)),
    InvoicedItem("invoiced item #2", Decimal(10), Decimal(25)),
    InvoicedItem("invoiced item #3", Decimal(5), Decimal(35)),
])

renderer = PdfInvoiceRenderer("invoice_ro-RO")
renderer.render(context, out_path)
