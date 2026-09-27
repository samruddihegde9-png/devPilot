"""
Unit tests for the three AI/scanner fixes:
  1. config._ENV_FILE is absolute (CWD-independent)
  2. _notebook_to_text converts .ipynb to readable text
  3. llm_available() reflects the key state correctly
"""
from __future__ import annotations

import json

import pytest


# ---------------------------------------------------------------------------
# Fix 1 — config: absolute .env path
# ---------------------------------------------------------------------------

def test_env_file_path_is_absolute():
    from app.config import _ENV_FILE
    assert _ENV_FILE.is_absolute(), (
        f"_ENV_FILE should be absolute so it works from any CWD; got: {_ENV_FILE}"
    )


def test_env_file_exists():
    from app.config import _ENV_FILE
    assert _ENV_FILE.exists(), (
        f"backend/.env does not exist at {_ENV_FILE}. Copy .env.example to .env."
    )


# ---------------------------------------------------------------------------
# Fix 2 — scanner: notebook conversion
# ---------------------------------------------------------------------------

def _make_nb(*cells: dict) -> str:
    return json.dumps({"cells": list(cells), "metadata": {}, "nbformat": 4})


def test_notebook_markdown_cell_extracted():
    from app.services.repo_intel.scanner import _notebook_to_text
    nb = _make_nb({"cell_type": "markdown", "source": ["# Hello\n", "Some text."]})
    result = _notebook_to_text(nb, "test.ipynb")
    assert "# Hello" in result
    assert "Some text." in result
    # Must not contain raw JSON structure
    assert '"cell_type"' not in result


def test_notebook_code_cell_fenced():
    from app.services.repo_intel.scanner import _notebook_to_text
    nb = _make_nb({"cell_type": "code", "source": ["import os\n", "print(os.getcwd())"]})
    result = _notebook_to_text(nb, "test.ipynb")
    assert "import os" in result
    assert "```python" in result


def test_notebook_raw_cell_included():
    from app.services.repo_intel.scanner import _notebook_to_text
    nb = _make_nb({"cell_type": "raw", "source": ["raw cell text"]})
    result = _notebook_to_text(nb, "test.ipynb")
    assert "raw cell text" in result


def test_notebook_list_source_joined():
    """nbformat <=4 stores source as a list of strings."""
    from app.services.repo_intel.scanner import _notebook_to_text
    nb = _make_nb({"cell_type": "code", "source": ["line1\n", "line2\n", "line3"]})
    result = _notebook_to_text(nb, "test.ipynb")
    assert "line1" in result
    assert "line2" in result
    assert "line3" in result


def test_notebook_empty_cells_returns_raw():
    from app.services.repo_intel.scanner import _notebook_to_text
    raw = json.dumps({"cells": [], "metadata": {}})
    result = _notebook_to_text(raw, "empty.ipynb")
    assert result == raw


def test_notebook_bad_json_returns_original():
    from app.services.repo_intel.scanner import _notebook_to_text
    bad = "not json at all {{{"
    result = _notebook_to_text(bad, "broken.ipynb")
    assert result == bad


def test_notebook_string_source_handled():
    """Some notebooks store source as a plain string, not a list."""
    from app.services.repo_intel.scanner import _notebook_to_text
    nb = json.dumps({
        "cells": [{"cell_type": "markdown", "source": "# Direct string source"}],
        "metadata": {},
    })
    result = _notebook_to_text(nb, "str_source.ipynb")
    assert "Direct string source" in result


# ---------------------------------------------------------------------------
# Fix 3 — llm: llm_available() reflects the key correctly
# ---------------------------------------------------------------------------

def test_llm_available_false_when_key_empty(monkeypatch):
    import app.services.repo_intel.llm as llm_mod
    monkeypatch.setattr(llm_mod.settings, "openai_api_key", "")
    assert llm_available() is False, "llm_available should be False when key is empty"


def test_llm_available_true_when_key_set(monkeypatch):
    import app.services.repo_intel.llm as llm_mod
    monkeypatch.setattr(llm_mod.settings, "openai_api_key", "sk-test-key-value")
    assert llm_available() is True, "llm_available should be True when key is non-empty"


def test_call_llm_returns_none_when_no_key(monkeypatch):
    import app.services.repo_intel.llm as llm_mod
    monkeypatch.setattr(llm_mod.settings, "openai_api_key", "")
    result = llm_mod.call_llm("sys", "user")
    assert result is None


# Import here so monkeypatch can reference it.
from app.services.repo_intel.llm import llm_available  # noqa: E402
