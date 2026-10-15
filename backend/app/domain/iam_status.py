from __future__ import annotations


def iam_auth_status_for_user_status(user_status: str) -> str:
    if user_status == "active":
        return "active"
    if user_status == "review":
        return "pending"
    return "blocked"
