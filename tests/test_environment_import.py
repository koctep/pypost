"""Tests for pypost.core.environment_import (PYPOST-986 / PYPOST-999).

Covers pure plan/conflict helpers and the Overwrite × ciphertext-reuse
round-trip lock
(`test_overwrite_import_reuses_unchanged_and_reencrypts_changed_hidden`).
"""

import pytest

import json
import unittest

from pypost.core.environment_import import (
    EnvironmentImportFileError,
    ImportConflictDecision,
    find_conflicts,
    generate_import_copy_name,
    load_import_candidates,
    plan_import,
)
from pypost.core.storage import StorageManager
from pypost.models.models import Environment
from pypost.models.settings import AppSettings

pytestmark = pytest.mark.timeout(60)


def _make_storage(tmp_path, monkeypatch) -> StorageManager:
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_ENABLED", raising=False)
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_KEY", raising=False)
    return StorageManager(data_dir=tmp_path / "pypost-data")


def test_load_import_candidates_happy_path_list(tmp_path, monkeypatch):
    storage = _make_storage(tmp_path, monkeypatch)
    import_file = tmp_path / "import.json"
    import_file.write_text(
        json.dumps(
            [
                {
                    "name": "Dev",
                    "variables": {"HOST": "dev.example.com"},
                    "hidden_keys": [],
                    "enable_mcp": False,
                },
                {
                    "name": "Prod",
                    "variables": {"HOST": "prod.example.com"},
                    "hidden_keys": [],
                    "enable_mcp": False,
                },
            ]
        ),
        encoding="utf-8",
    )

    environments, parse_errors = load_import_candidates(import_file, storage)

    assert parse_errors == []
    assert [env.name for env in environments] == ["Dev", "Prod"]
    assert all(isinstance(env, Environment) for env in environments)


def test_load_import_candidates_normalizes_single_object(tmp_path, monkeypatch):
    storage = _make_storage(tmp_path, monkeypatch)
    import_file = tmp_path / "import.json"
    import_file.write_text(
        json.dumps({"name": "Solo", "variables": {"HOST": "solo.example.com"}}),
        encoding="utf-8",
    )

    environments, parse_errors = load_import_candidates(import_file, storage)

    assert parse_errors == []
    assert len(environments) == 1
    assert environments[0].name == "Solo"


def test_load_import_candidates_raises_on_malformed_json(tmp_path, monkeypatch):
    storage = _make_storage(tmp_path, monkeypatch)
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(EnvironmentImportFileError):
        load_import_candidates(bad_file, storage)


def test_load_import_candidates_rejects_duplicate_json_keys(tmp_path, monkeypatch):
    storage = _make_storage(tmp_path, monkeypatch)
    import_file = tmp_path / "duplicate.json"
    import_file.write_text(
        '{"name":"Dev","variables":{"A":"1","A":"2"}}',
        encoding="utf-8",
    )

    with pytest.raises(EnvironmentImportFileError, match="Duplicate JSON key"):
        load_import_candidates(import_file, storage)


def test_load_import_candidates_reports_normalized_duplicate_key(tmp_path, monkeypatch):
    storage = _make_storage(tmp_path, monkeypatch)
    import_file = tmp_path / "duplicate-normalized.json"
    import_file.write_text(
        json.dumps({"name": "Dev", "variables": {"A": "1", " A ": "2"}}),
        encoding="utf-8",
    )

    environments, parse_errors = load_import_candidates(import_file, storage)

    assert environments == []
    assert len(parse_errors) == 1
    assert 'Variable "A" already exists.' in parse_errors[0]


def test_load_import_candidates_reports_partial_decrypt_failure(tmp_path, monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    storage = _make_storage(tmp_path, monkeypatch)
    original_key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", original_key)
    settings = AppSettings(env_encryption_enabled=True)
    storage.apply_encryption_settings(settings)

    storage.save_environments(
        [
            Environment(
                id="e1",
                name="Secret",
                variables={"TOKEN": "s3cr3t"},
                hidden_keys={"TOKEN"},
            ),
            Environment(id="e2", name="Plain", variables={"HOST": "example.com"}),
        ]
    )
    import_file = tmp_path / "import.json"
    import_file.write_text(
        storage.environments_file.read_text(encoding="utf-8"), encoding="utf-8"
    )

    different_key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", different_key)
    storage.apply_encryption_settings(settings)

    environments, parse_errors = load_import_candidates(import_file, storage)

    assert [env.name for env in environments] == ["Plain"]
    assert len(parse_errors) == 1
    assert "Secret" in parse_errors[0]


class TestFindConflicts(unittest.TestCase):
    def test_returns_intersection_in_incoming_order_without_duplicates(self) -> None:
        existing = [Environment(name="Dev"), Environment(name="Prod")]
        incoming = [
            Environment(name="Staging"),
            Environment(name="Prod"),
            Environment(name="Prod"),
            Environment(name="Dev"),
        ]

        self.assertEqual(find_conflicts(existing, incoming), ["Prod", "Dev"])

    def test_no_conflicts_returns_empty_list(self) -> None:
        existing = [Environment(name="Dev")]
        incoming = [Environment(name="Staging")]

        self.assertEqual(find_conflicts(existing, incoming), [])


class TestGenerateImportCopyName(unittest.TestCase):
    def test_returns_copy_of_name_when_free(self) -> None:
        self.assertEqual(generate_import_copy_name("Dev", set()), "Copy of Dev")

    def test_returns_numbered_copy_when_first_taken(self) -> None:
        self.assertEqual(
            generate_import_copy_name("Dev", {"Copy of Dev"}), "Copy of Dev (2)"
        )

    def test_returns_next_numbered_copy_when_first_two_taken(self) -> None:
        self.assertEqual(
            generate_import_copy_name("Dev", {"Copy of Dev", "Copy of Dev (2)"}),
            "Copy of Dev (3)",
        )

    def test_returns_next_numbered_copy_when_first_three_taken(self) -> None:
        self.assertEqual(
            generate_import_copy_name(
                "Dev", {"Copy of Dev", "Copy of Dev (2)", "Copy of Dev (3)"}
            ),
            "Copy of Dev (4)",
        )


class TestPlanImportOverwrite(unittest.TestCase):
    def test_preserves_existing_id_and_position(self) -> None:
        existing_dev = Environment(id="existing-dev-id", name="Dev", variables={"A": "1"})
        existing_prod = Environment(id="existing-prod-id", name="Prod", variables={"B": "2"})
        existing = [existing_dev, existing_prod]
        incoming = [
            Environment(
                name="Dev",
                variables={"A": "new"},
                hidden_keys={"A"},
                enable_mcp=True,
            )
        ]

        result = plan_import(existing, incoming, {"Dev": ImportConflictDecision.OVERWRITE})

        self.assertEqual(
            [env.id for env in result.environments],
            ["existing-dev-id", "existing-prod-id"],
        )
        updated = result.environments[0]
        self.assertEqual(updated.variables, {"A": "new"})
        self.assertEqual(updated.hidden_keys, {"A"})
        self.assertTrue(updated.enable_mcp)
        self.assertEqual(result.updated, ["Dev"])


def test_overwrite_import_reuses_unchanged_and_reencrypts_changed_hidden(
    tmp_path, monkeypatch
):
    """PYPOST-999: Overwrite import × save × reload locks ciphertext reuse.

    Verification debt: expected green against current production (no product
    change intended). Proves unchanged Hidden keeps the same on-disk envelope
    after Overwrite; changed Hidden gets a new envelope and reloads correctly.
    """
    fernet = pytest.importorskip("cryptography.fernet")
    key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_ENABLED", "true")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", key)

    storage = StorageManager(data_dir=tmp_path / "pypost-data")
    settings = AppSettings(env_encryption_enabled=True)
    storage.apply_encryption_settings(settings)

    initial = Environment(
        id="existing-dev-id",
        name="Dev",
        variables={"KEEP": "same-secret", "CHANGE": "old-secret"},
        hidden_keys={"KEEP", "CHANGE"},
    )
    storage.save_environments([initial])

    with open(storage.environments_file, "r", encoding="utf-8") as handle:
        pre_payload = json.load(handle)
    pre_vars = pre_payload[0]["variables"]
    keep_envelope_before = pre_vars["KEEP"]
    change_envelope_before = pre_vars["CHANGE"]
    assert isinstance(keep_envelope_before, dict) and keep_envelope_before.get("enc") is True
    assert (
        isinstance(change_envelope_before, dict) and change_envelope_before.get("enc") is True
    )

    incoming = [
        Environment(
            name="Dev",
            variables={"KEEP": "same-secret", "CHANGE": "new-secret"},
            hidden_keys={"KEEP", "CHANGE"},
        )
    ]
    result = plan_import([initial], incoming, {"Dev": ImportConflictDecision.OVERWRITE})
    planned = result.environments[0]
    assert planned.id == "existing-dev-id"

    stats = storage.save_environments(result.environments)
    assert stats.reused_count >= 1
    assert stats.encrypted_count >= 1

    with open(storage.environments_file, "r", encoding="utf-8") as handle:
        post_payload = json.load(handle)
    post_vars = post_payload[0]["variables"]
    keep_envelope_after = post_vars["KEEP"]
    change_envelope_after = post_vars["CHANGE"]

    assert keep_envelope_after == keep_envelope_before
    assert change_envelope_after != change_envelope_before
    assert isinstance(change_envelope_after, dict) and change_envelope_after.get("enc") is True

    reloaded = storage.load_environments()
    assert len(reloaded) == 1
    assert reloaded[0].id == "existing-dev-id"
    assert reloaded[0].variables["KEEP"] == "same-secret"
    assert reloaded[0].variables["CHANGE"] == "new-secret"


class TestPlanImportKeepBoth(unittest.TestCase):
    def test_appends_renamed_copy_and_leaves_existing_untouched(self) -> None:
        existing_dev = Environment(id="existing-dev-id", name="Dev", variables={"A": "1"})
        existing = [existing_dev]
        incoming = [Environment(name="Dev", variables={"A": "new"})]

        result = plan_import(existing, incoming, {"Dev": ImportConflictDecision.KEEP_BOTH})

        self.assertEqual(len(result.environments), 2)
        untouched = result.environments[0]
        self.assertEqual(untouched.id, "existing-dev-id")
        self.assertEqual(untouched.variables, {"A": "1"})
        new_env = result.environments[1]
        self.assertEqual(new_env.name, "Copy of Dev")
        self.assertNotEqual(new_env.id, existing_dev.id)
        self.assertEqual(result.renamed, [("Dev", "Copy of Dev")])


class TestPlanImportDuplicateNamesWithinFile(unittest.TestCase):
    def test_three_duplicate_names_report_two_renames_each(self) -> None:
        existing: list[Environment] = []
        incoming = [
            Environment(name="Dev"),
            Environment(name="Dev"),
            Environment(name="Dev"),
        ]

        result = plan_import(existing, incoming, {})

        self.assertEqual(
            [env.name for env in result.environments],
            ["Dev", "Copy of Dev", "Copy of Dev (2)"],
        )
        self.assertEqual(result.added, ["Dev"])
        self.assertEqual(
            result.renamed, [("Dev", "Copy of Dev"), ("Dev", "Copy of Dev (2)")]
        )
        self.assertEqual(len(result.renamed), 2)


class TestPlanImportSkip(unittest.TestCase):
    def test_leaves_environments_identical_for_skipped_name(self) -> None:
        existing_dev = Environment(id="existing-dev-id", name="Dev", variables={"A": "1"})
        existing = [existing_dev]
        incoming = [Environment(name="Dev", variables={"A": "new"})]

        result = plan_import(existing, incoming, {"Dev": ImportConflictDecision.SKIP})

        self.assertEqual(len(result.environments), 1)
        self.assertEqual(result.environments[0].id, "existing-dev-id")
        self.assertEqual(result.environments[0].variables, {"A": "1"})
        self.assertEqual(result.skipped, ["Dev"])


class TestPlanImportNonConflicting(unittest.TestCase):
    def test_non_conflicting_name_always_added_regardless_of_other_decisions(self) -> None:
        existing = [Environment(id="existing-dev-id", name="Dev", variables={"A": "1"})]
        incoming = [Environment(name="Staging", variables={"B": "2"})]

        result = plan_import(
            existing, incoming, {"SomeOtherName": ImportConflictDecision.SKIP}
        )

        self.assertEqual(len(result.environments), 2)
        self.assertEqual(result.added, ["Staging"])
        self.assertEqual(result.environments[1].name, "Staging")


if __name__ == "__main__":
    unittest.main()
