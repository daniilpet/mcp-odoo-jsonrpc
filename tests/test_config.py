import os

from mcp_odoo_jsonrpc.config import TrustMode, _parse_trust_mode, _parse_allowed_projects


def test_trust_mode_default_restricted(monkeypatch):
    monkeypatch.delenv("ODOO_TRUST_MODE", raising=False)
    assert _parse_trust_mode() == TrustMode.RESTRICTED


def test_trust_mode_full(monkeypatch):
    monkeypatch.setenv("ODOO_TRUST_MODE", "full")
    assert _parse_trust_mode() == TrustMode.FULL


def test_trust_mode_unknown_defaults(monkeypatch):
    monkeypatch.setenv("ODOO_TRUST_MODE", "banana")
    assert _parse_trust_mode() == TrustMode.RESTRICTED


def test_allowed_projects_empty(monkeypatch):
    monkeypatch.delenv("ODOO_ALLOWED_PROJECTS", raising=False)
    assert _parse_allowed_projects() is None


def test_allowed_projects_set(monkeypatch):
    monkeypatch.setenv("ODOO_ALLOWED_PROJECTS", "99,101,200")
    result = _parse_allowed_projects()
    assert result == [99, 101, 200]


def test_allowed_projects_single(monkeypatch):
    monkeypatch.setenv("ODOO_ALLOWED_PROJECTS", "99")
    result = _parse_allowed_projects()
    assert result == [99]
