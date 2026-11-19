import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.scripts import seed_iam_rbac


@pytest.mark.parametrize("drift", [False, True])
def test_strict_rbac_report_detects_drift_without_seeding(monkeypatch, drift):
    matrix = seed_iam_rbac.build_rbac_matrix()
    if drift:
        matrix.pop(next(iter(matrix)))
    iam = SimpleNamespace(rbac_report=AsyncMock(return_value=matrix), seed_rbac=AsyncMock())
    monkeypatch.setattr(seed_iam_rbac, "IamClient", lambda: iam)
    monkeypatch.setattr(sys, "argv", ["seed_iam_rbac", "--report", "--strict"])
    if drift:
        with pytest.raises(SystemExit) as exc:
            seed_iam_rbac.main()
        assert exc.value.code == 2
    else:
        seed_iam_rbac.main()
    iam.seed_rbac.assert_not_awaited()


def test_strict_without_report_cannot_mutate_iam(monkeypatch):
    client = AsyncMock()
    monkeypatch.setattr(seed_iam_rbac, "IamClient", client)
    monkeypatch.setattr(sys, "argv", ["seed_iam_rbac", "--strict"])
    with pytest.raises(SystemExit) as exc:
        seed_iam_rbac.main()
    assert exc.value.code == 2
    client.assert_not_called()
