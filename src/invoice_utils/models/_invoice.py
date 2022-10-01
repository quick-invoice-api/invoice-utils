from dataclasses import dataclass, Field
from decimal import Decimal


@dataclass
class InvoicedItem:
    text: str = Field(
        default="",
        default_factory=None,
        init=True,
        repr=True,
        hash=True,
        compare=True,
        metadata=None,
        kw_only=False,
    )
    quantity: Decimal = Field(
        default=1,
        default_factory=None,
        init=True,
        repr=True,
        hash=True,
        compare=False,
        metadata=None,
        kw_only=False,
    )
    unit_price: Decimal = Field(
        default=0,
        default_factory=None,
        init=True,
        repr=True,
        hash=True,
        compare=True,
        metadata=None,
        kw_only=False,
    )
