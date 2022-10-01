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
context = engine.process(1, datetime.now(), [InvoicedItem("invoiced item", Decimal(20), Decimal(719))])

renderer = PdfInvoiceRenderer("invoice")
renderer.render(context, out_path)
