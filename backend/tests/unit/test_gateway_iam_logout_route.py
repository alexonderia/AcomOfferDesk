from pathlib import Path


def test_gateway_routes_bff_iam_logout_to_backend() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    config = (repo_root / "deploy/k8s/acom/config/gateway-nginx.conf").read_text()
    assert "location = /iam/acom/logout" in config
    block = config.split("location = /iam/acom/logout", 1)[1].split("}", 1)[0]
    assert "proxy_pass http://backend:8000;" in block
