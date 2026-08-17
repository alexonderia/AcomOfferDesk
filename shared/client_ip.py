from __future__ import annotations

import ipaddress
from collections.abc import Iterable


def _parse_address(value: str | None) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    if value is None:
        return None
    candidate = value.strip()
    if not candidate:
        return None
    try:
        return ipaddress.ip_address(candidate)
    except ValueError:
        return None


def resolve_client_ip(
    *,
    peer_host: str | None,
    forwarded_for: str | None,
    real_ip: str | None,
    trusted_proxy_cidrs: Iterable[str],
) -> str | None:
    peer = _parse_address(peer_host)
    if peer is None:
        return peer_host.strip() if peer_host and peer_host.strip() else None

    trusted_networks = tuple(
        ipaddress.ip_network(cidr.strip(), strict=False)
        for cidr in trusted_proxy_cidrs
        if cidr.strip()
    )
    if not any(peer in network for network in trusted_networks):
        return str(peer)

    forwarded_addresses = [
        address
        for address in (
            _parse_address(item)
            for item in (forwarded_for or "").split(",")
        )
        if address is not None
    ]
    if forwarded_addresses:
        for address in reversed(forwarded_addresses):
            if not any(address in network for network in trusted_networks):
                return str(address)
        return str(forwarded_addresses[0])

    resolved_real_ip = _parse_address(real_ip)
    return str(resolved_real_ip or peer)
