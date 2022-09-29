from datetime import datetime
from decimal import Decimal
from pathlib import Path

from invoice_utils._adt import InvoicedItem
from invoice_utils._engine import InvoicingEngine
from invoice_utils._render import Renderer


templates_dir = Path(__file__).parent / "templates"
basic_invoice_data_template = templates_dir / "basic.json"

engine = InvoicingEngine(str(basic_invoice_data_template))
context = engine.process(1, datetime.now(), [InvoicedItem("invoiced item", Decimal(20), Decimal(719))])

renderer = Renderer("invoice")
renderer.render(context)
