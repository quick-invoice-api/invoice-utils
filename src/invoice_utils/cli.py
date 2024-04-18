import json
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

import arrow
from typer import run, Option, Argument

from invoice_utils.engine import InvoicingEngine
from invoice_utils.models import InvoicedItem
from invoice_utils.render import PdfInvoiceRenderer


_ROOT_DIR = Path(__file__).parent


class RenderTemplate(StrEnum):
    BASE = "invoice"
    ROMANIAN = "invoice_ro-RO"


def _load_invoiced_items(obj: list) -> tuple[Any, datetime, list[InvoicedItem]]:
    invoice_no = obj[0]
    invoice_date = arrow.get(obj[1]).datetime

    items = [InvoicedItem(**item_obj) for item_obj in obj[2]]
    return invoice_no, invoice_date, items


def _make_invoices(
    invoices: Path = Argument(..., file_okay=True, exists=True, dir_okay=False, help="JSON file containing invoiced items"),
    invoice_template: Path = Option(
        _ROOT_DIR / "basic.json", "-t", "--template", help="JSON template containing the invoicing rules",
        file_okay=True, exists=True, dir_okay=False
    ),
    output_dir: Path = Option(
        _ROOT_DIR.parent.parent / "invoices", "-o", "--output-dir", help="Directory where the invoice files will be generated",
        file_okay=False, dir_okay=True, exists=False
    ),
    render_template: RenderTemplate = Option(RenderTemplate.BASE, "-r", "--render-template", help="Rendering template to use"),
) -> int:
    with open(invoice_template, "r") as f:
        engine = InvoicingEngine(json.load(f))
    with open(invoices, "r") as f:
        invoiced_items = map(_load_invoiced_items, json.load(f))

    output_dir.mkdir(0o755, True, True)
    for invoice in invoiced_items:
        context = engine.process(*invoice)
        renderer = PdfInvoiceRenderer(render_template)
        out_path = output_dir / f"{invoice[1]:%Y%m%d}-{invoice[0]:04}-invoice.pdf"
        renderer.render(context, str(out_path), persist=True)
    return 0


def run_command():
    run(_make_invoices)