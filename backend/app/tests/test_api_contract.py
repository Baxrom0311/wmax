from __future__ import annotations

from pathlib import Path

import yaml

from app.main import app


REQUIRED_CONTRACT_PATHS = {
    "/api/v1/auth/request-code",
    "/api/v1/auth/verify-code",
    "/api/v1/auth/refresh",
    "/api/v1/auth/logout",
    "/api/v1/auth/me",
    "/api/v1/patients",
    "/api/v1/patients/{id}",
    "/api/v1/patients/{id}/timeline",
    "/api/v1/patients/{id}/readings",
    "/api/v1/patients/{id}/baseline",
    "/api/v1/patients/{id}/baseline/approve",
    "/api/v1/patients/{id}/deceased",
    "/api/v1/patients/{id}/memberships",
    "/api/v1/patients/{id}/memberships/{mid}",
    "/api/v1/patients/{id}/memberships/{mid}/baseline-decision",
    "/api/v1/patients/{id}/access/invite",
    "/api/v1/access/accept",
    "/api/v1/patients/{id}/access/{aid}",
    "/api/v1/patients/{id}/consents",
    "/api/v1/patients/{id}/consents/{cid}/revoke",
    "/api/v1/devices",
    "/api/v1/devices/enroll",
    "/api/v1/devices/{device_id}/assign",
    "/api/v1/devices/{device_id}/release",
    "/api/v1/devices/{device_id}/revoke-credential",
    "/api/v1/devices/{device_id}/health",
    "/api/v1/ingest/readings",
    "/api/v1/ingest/sos",
    "/api/v1/orphans",
    "/api/v1/orphans/{id}/candidates",
    "/api/v1/orphans/{id}/resolve",
    "/api/v1/orphans/{id}/discard",
    "/api/v1/alerts",
    "/api/v1/tasks",
    "/api/v1/tasks/{id}/acknowledge",
    "/api/v1/tasks/{id}/complete",
    "/api/v1/tasks/{id}/reassign",
    "/api/v1/sos",
    "/api/v1/patients/{id}/subscription",
    "/api/v1/patients/{id}/subscription/checkout",
    "/api/v1/webhooks/payments/{provider}",
    "/api/v1/tenants/{id}/licence",
    "/api/v1/tenants/{id}/usage",
    "/api/v1/tenants/{id}/invoices",
    "/api/v1/surveys/pending",
    "/api/v1/surveys/{id}",
    "/api/v1/surveys/{id}/submit",
    "/api/v1/platform/research/cohort",
    "/api/v1/platform/support/patients/{id}",
    "/api/v1/platform/access-log",
    "/api/v1/realtime/status",
    "/api/v1/realtime/events",
    "/api/v1/health",
    "/api/v1/health/ready",
    "/api/v1/metrics",
}

REQUIRED_CONTRACT_OPERATIONS = {
    ("/api/v1/auth/request-code", "post"),
    ("/api/v1/auth/verify-code", "post"),
    ("/api/v1/auth/refresh", "post"),
    ("/api/v1/auth/logout", "post"),
    ("/api/v1/auth/me", "get"),
    ("/api/v1/patients", "get"),
    ("/api/v1/patients", "post"),
    ("/api/v1/patients/{id}", "get"),
    ("/api/v1/patients/{id}", "patch"),
    ("/api/v1/patients/{id}/timeline", "get"),
    ("/api/v1/patients/{id}/readings", "get"),
    ("/api/v1/patients/{id}/baseline", "get"),
    ("/api/v1/patients/{id}/baseline/approve", "post"),
    ("/api/v1/patients/{id}/deceased", "post"),
    ("/api/v1/patients/{id}/memberships", "post"),
    ("/api/v1/patients/{id}/memberships/{mid}", "delete"),
    ("/api/v1/patients/{id}/memberships/{mid}/baseline-decision", "post"),
    ("/api/v1/patients/{id}/access/invite", "post"),
    ("/api/v1/access/accept", "post"),
    ("/api/v1/patients/{id}/access/{aid}", "delete"),
    ("/api/v1/patients/{id}/consents", "get"),
    ("/api/v1/patients/{id}/consents", "post"),
    ("/api/v1/patients/{id}/consents/{cid}/revoke", "post"),
    ("/api/v1/devices", "get"),
    ("/api/v1/devices", "post"),
    ("/api/v1/devices/enroll", "post"),
    ("/api/v1/devices/{device_id}/assign", "post"),
    ("/api/v1/devices/{device_id}/release", "post"),
    ("/api/v1/devices/{device_id}/revoke-credential", "post"),
    ("/api/v1/devices/{device_id}/health", "get"),
    ("/api/v1/ingest/readings", "post"),
    ("/api/v1/ingest/sos", "post"),
    ("/api/v1/orphans", "get"),
    ("/api/v1/orphans/{id}/candidates", "get"),
    ("/api/v1/orphans/{id}/resolve", "post"),
    ("/api/v1/orphans/{id}/discard", "post"),
    ("/api/v1/alerts", "get"),
    ("/api/v1/tasks", "get"),
    ("/api/v1/tasks/{id}/acknowledge", "post"),
    ("/api/v1/tasks/{id}/complete", "post"),
    ("/api/v1/tasks/{id}/reassign", "post"),
    ("/api/v1/sos", "post"),
    ("/api/v1/patients/{id}/subscription", "get"),
    ("/api/v1/patients/{id}/subscription/checkout", "post"),
    ("/api/v1/webhooks/payments/{provider}", "post"),
    ("/api/v1/tenants/{id}/licence", "get"),
    ("/api/v1/tenants/{id}/usage", "get"),
    ("/api/v1/tenants/{id}/invoices", "get"),
    ("/api/v1/surveys/pending", "get"),
    ("/api/v1/surveys/{id}", "get"),
    ("/api/v1/surveys/{id}/submit", "post"),
    ("/api/v1/platform/research/cohort", "get"),
    ("/api/v1/platform/support/patients/{id}", "get"),
    ("/api/v1/platform/access-log", "get"),
    ("/api/v1/realtime/status", "get"),
    ("/api/v1/realtime/events", "get"),
    ("/api/v1/health", "get"),
    ("/api/v1/health/ready", "get"),
    ("/api/v1/metrics", "get"),
}


def test_architecture_contract_paths_are_exposed():
    schema = app.openapi()
    paths = set(schema["paths"])

    assert REQUIRED_CONTRACT_PATHS - paths == set()


def test_architecture_contract_operations_are_exposed():
    schema = app.openapi()
    operations = {
        (path, method)
        for path, methods in schema["paths"].items()
        for method in methods
        if method in {"get", "post", "patch", "delete"}
    }

    assert REQUIRED_CONTRACT_OPERATIONS - operations == set()


def test_legacy_ingest_endpoint_is_not_in_public_openapi():
    schema = app.openapi()

    assert "/api/v1/ingest" not in schema["paths"]


def test_openapi_contract_file_matches_app_paths():
    schema = app.openapi()
    contract_path = Path(__file__).resolve().parents[3] / "contracts" / "openapi.yaml"
    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))

    assert set(contract["paths"]) == set(schema["paths"])


def test_openapi_contract_file_matches_app_operations():
    schema = app.openapi()
    contract_path = Path(__file__).resolve().parents[3] / "contracts" / "openapi.yaml"
    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))

    def operations(doc: dict) -> set[tuple[str, str]]:
        return {
            (path, method)
            for path, methods in doc["paths"].items()
            for method in methods
            if method in {"get", "post", "patch", "delete"}
        }

    assert operations(contract) == operations(schema)


def test_openapi_contract_file_matches_app_schema_components():
    schema = app.openapi()
    contract_path = Path(__file__).resolve().parents[3] / "contracts" / "openapi.yaml"
    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))

    assert set(contract.get("components", {}).get("schemas", {})) == set(
        schema.get("components", {}).get("schemas", {})
    )
