"""Tests for derived routing metadata and provenance."""

from __future__ import annotations

from harnessctl.routing.derived import derive_task_metadata


def test_derives_metadata_from_minimal_request() -> None:
    result = derive_task_metadata(
        {
            "prompt": "Design an LLD for distributed lock manager",
        }
    )

    assert result["derived"]["task_class"] == "architecture"
    assert result["derived"]["risk"] == "high"
    assert result["derived"]["complexity"] >= 35
    assert result["derived"]["required_capabilities"] == ["design", "reasoning"]

    assert result["provenance"] == {
        "task_class": "inferred",
        "required_capabilities": "inferred",
        "risk": "inferred",
        "complexity": "inferred",
    }


def test_respects_hints_constraints_and_provenance() -> None:
    result = derive_task_metadata(
        {
            "prompt": "Design an LLD for distributed lock manager",
            "task_type": "lld",
            "hints": {"risk": "high", "complexity": 75},
            "constraints": {
                "user_required_capabilities": [
                    "reasoning",
                    "design",
                    "security_analysis",
                ]
            },
        }
    )

    assert result["derived"]["task_class"] == "lld"
    assert result["derived"]["risk"] == "high"
    assert result["derived"]["complexity"] == 75
    assert result["derived"]["required_capabilities"] == [
        "design",
        "reasoning",
        "security_analysis",
    ]

    assert result["provenance"] == {
        "task_class": "caller_hint",
        "required_capabilities": "inferred+user_add",
        "risk": "caller_hint",
        "complexity": "caller_hint",
    }


def test_applies_taxonomy_alias_when_task_type_provided() -> None:
    routing_config = {
        "spec": {
            "taxonomy": {
                "aliases": {
                    "ui": "frontend",
                }
            }
        }
    }

    result = derive_task_metadata(
        {
            "prompt": "Implement a UI profile editor",
            "task_type": "ui",
        },
        routing_config=routing_config,
    )

    assert result["derived"]["task_class"] == "frontend"
    assert result["provenance"]["task_class"] == "caller_hint_alias"
