from __future__ import annotations

from decimal import Decimal, InvalidOperation

from app.domain.exceptions import Conflict


# All persisted request, offer and plan amounts use NUMERIC(14, 2).
MAX_AMOUNT = Decimal("999999999999.99")


def validate_amount(value: Decimal | float | int | str) -> Decimal:
    """Validate money before comparisons, rounding or persistence."""
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise Conflict("Укажите корректную сумму") from None
    if not amount.is_finite():
        raise Conflict("Сумма должна быть конечным числом")
    if amount < 0:
        raise Conflict("Сумма не может быть отрицательной")
    if amount > MAX_AMOUNT:
        raise Conflict("Сумма превышает допустимое значение 999999999999,99")
    return amount
