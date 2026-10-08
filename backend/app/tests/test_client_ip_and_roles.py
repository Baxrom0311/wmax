from __future__ import annotations

from types import SimpleNamespace

from starlette.requests import Request

from app.auth.router import _client_ip
from app.auth.service import _primary_clinician_role


def _request(peer: str, headers: dict[str, str]) -> Request:
    return Request(
        {
            "type": "http",
            "client": (peer, 1234),
            "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
        }
    )


def test_spoofed_forwarded_for_from_public_peer_is_ignored():
    req = _request("8.8.4.4", {"X-Forwarded-For": "1.2.3.4"})
    assert _client_ip(req) == "8.8.4.4"


def test_proxy_uses_rightmost_forwarded_entry_not_client_supplied_one():
    req = _request("172.18.0.1", {"X-Forwarded-For": "1.2.3.4, 198.51.100.7"})
    assert _client_ip(req) == "198.51.100.7"


def test_proxy_real_ip_header_wins():
    req = _request(
        "127.0.0.1",
        {"X-Real-IP": "198.51.100.7", "X-Forwarded-For": "1.2.3.4, 198.51.100.7"},
    )
    assert _client_ip(req) == "198.51.100.7"


def _members(*roles: str) -> list[SimpleNamespace]:
    return [SimpleNamespace(role=role) for role in roles]


def test_head_doctor_receives_doctor_token_role():
    assert _primary_clinician_role(_members("head_doctor")) == "doctor"


def test_role_choice_is_deterministic_across_memberships():
    assert _primary_clinician_role(_members("nurse", "doctor")) == "doctor"
    assert _primary_clinician_role(_members("doctor", "nurse")) == "doctor"
    assert _primary_clinician_role(_members("nurse", "admin")) == "admin"


def test_no_membership_yields_no_role():
    assert _primary_clinician_role([]) is None
