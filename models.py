"""Domain models, validation rules and formatting helpers for PennyTrack.

This module has no dependency on the database or the UI, so it can be
reused and tested on its own.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

CURRENCY_SYMBOL = "\u20b9"  # Indian Rupee sign

INCOME = "income"
EXPENSE = "expense"
TRANSACTION_TYPES = (INCOME, EXPENSE)

INCOME_CATEGORIES = [
    "Salary",
    "Freelance",
    "Business",
    "Investments",
    "Interest",
    "Gift",
    "Refund",
    "Other Income",
]

EXPENSE_CATEGORIES = [
    "Food & Dining",
    "Groceries",
    "Rent",
    "Utilities",
    "Transport",
    "Fuel",
    "Shopping",
    "Health",
    "Education",
    "Entertainment",
    "Travel",
    "Bills & EMI",
    "Other Expense",
]

MAX_AMOUNT = Decimal("9999999999.99")  # just under 1,000 crore
MAX_CATEGORY_LENGTH = 50
MAX_DESCRIPTION_LENGTH = 200
MIN_DATE = date(2000, 1, 1)

_AMOUNT_PATTERN = re.compile(r"\d+(\.\d{1,2})?|\.\d{1,2}")


class ValidationError(ValueError):
    """Raised when user-supplied transaction data is invalid."""


@dataclass
class Transaction:
    """A single income or expense record."""

    type: str
    amount: Decimal
    category: str
    description: str
    date: date
    id: Optional[int] = None


@dataclass
class Summary:
    """Aggregated totals shown on the dashboard."""

    total_income: Decimal = Decimal("0.00")
    total_expenses: Decimal = Decimal("0.00")

    @property
    def balance(self) -> Decimal:
        return self.total_income - self.total_expenses


def parse_amount(text: str) -> Decimal:
    """Convert user text into a valid positive rupee amount.

    Accepts digits with an optional decimal part of at most two places.
    A leading rupee sign, spaces and thousands commas are ignored.
    """
    cleaned = (text or "").replace(CURRENCY_SYMBOL, "").replace(",", "").replace(" ", "").strip()
    if not cleaned:
        raise ValidationError("Please enter an amount.")
    if not _AMOUNT_PATTERN.fullmatch(cleaned):
        raise ValidationError(
            "Amount must be a positive number with at most 2 decimal places (for example 1250.50)."
        )
    value = Decimal(cleaned)
    if value <= 0:
        raise ValidationError("Amount must be greater than zero.")
    if value > MAX_AMOUNT:
        raise ValidationError("Amount is too large.")
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def build_transaction(
    tx_type: str,
    amount_text: str,
    category: str,
    description: str,
    tx_date: date,
    tx_id: Optional[int] = None,
) -> Transaction:
    """Validate raw form values and return a clean Transaction.

    Raises ValidationError with a user-friendly message on any problem.
    """
    if tx_type not in TRANSACTION_TYPES:
        raise ValidationError("Please choose Income or Expense.")

    amount = parse_amount(amount_text)

    category = " ".join((category or "").split())
    if not category:
        raise ValidationError("Please choose or enter a category.")
    if len(category) > MAX_CATEGORY_LENGTH:
        raise ValidationError(f"Category must be at most {MAX_CATEGORY_LENGTH} characters.")

    description = " ".join((description or "").split())
    if len(description) > MAX_DESCRIPTION_LENGTH:
        raise ValidationError(f"Description must be at most {MAX_DESCRIPTION_LENGTH} characters.")

    if not isinstance(tx_date, date):
        raise ValidationError("Please choose a valid date.")
    if tx_date > date.today():
        raise ValidationError("The date cannot be in the future.")
    if tx_date < MIN_DATE:
        raise ValidationError(f"The date cannot be earlier than {MIN_DATE:%d %b %Y}.")

    return Transaction(
        type=tx_type,
        amount=amount,
        category=category,
        description=description,
        date=tx_date,
        id=tx_id,
    )


def format_inr(amount: Decimal) -> str:
    """Format an amount in Indian Rupees using lakh/crore digit grouping.

    Example: Decimal('1234567.5') -> '\u20b912,34,567.50'
    """
    value = Decimal(amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    sign = "-" if value < 0 else ""
    whole, fraction = f"{abs(value):.2f}".split(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        whole = ",".join(groups + [tail])
    return f"{sign}{CURRENCY_SYMBOL}{whole}.{fraction}"
