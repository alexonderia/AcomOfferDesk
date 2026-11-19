from decimal import Decimal

import pytest

from app.domain.exceptions import Conflict
from app.services.offers import OfferService
from app.services.plans import normalize_amount
from app.services.requests import RequestService


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf"), -1, 1e12, 1e100])
@pytest.mark.parametrize("kind", ["request", "offer", "plan"])
def test_invalid_amounts_are_rejected_by_each_service(kind, value):
    with pytest.raises(Conflict):
        if kind == "request":
            RequestService._validate_amount(None, value=value, field_name="Initial amount")
        elif kind == "offer":
            OfferService._validate_offer_amount(None, value)
        else:
            normalize_amount(value)


@pytest.mark.parametrize("value", [0, 1, Decimal("999999999999.99")])
def test_valid_money_boundaries_are_preserved(value):
    RequestService._validate_amount(None, value=value, field_name="Final amount")
    OfferService._validate_offer_amount(None, value)
    assert normalize_amount(value) == Decimal(str(value)).quantize(Decimal("0.01"))


def test_plan_amount_rounding_is_preserved():
    assert normalize_amount("1.005") == Decimal("1.01")
