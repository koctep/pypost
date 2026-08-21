"""Tests for pypost.core.collection_import (PYPOST-987).

Started as the Step 3 failing repro for Import Collection and now covers the
pure planning logic: file parsing, per-record shape errors, conflict detection,
overwrite / keep-both / skip outcomes, id-collision handling, and the summary
text shown in the result dialog.
"""

import json
import unittest

import pytest

from pypost.core.collection_import import (
    CollectionImportFileError,
    find_collection_conflicts,
    format_collection_import_result,
    load_collection_import_candidates,
    plan_collection_import,
    recount_collection_import_plan,
)

from pypost.core.import_conflicts import ImportConflictDecision
from pypost.models.models import Collection, RequestData

pytestmark = pytest.mark.timeout(30)


def _request_record(**overrides) -> dict:
    record = {
        "id": "req-1",
        "name": "List users",
        "method": "POST",
        "url": "https://api.example.com/users",
        "headers": {"Authorization": "Bearer {{token}}"},
        "params": {"page": "1"},
        "body": '{"q": 1}',
        "body_type": "json",
        "post_script": "print(response.status_code)",
        "expose_as_mcp": True,
        "mcp_description": "List all users",
        "mcp_params": {"page": {"type": "integer", "description": "Page", "required": False}},
    }
    record.update(overrides)
    return record


def _collection_record(**overrides) -> dict:
    record = {
        "id": "col-1",
        "name": "My API",
        "requests": [_request_record()],
    }
    record.update(overrides)
    return record


def _write(tmp_path, payload, filename: str = "import.json"):
    path = tmp_path / filename
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _make_collection(col_id: str, name: str, requests=None) -> Collection:
    return Collection(id=col_id, name=name, requests=requests or [])


def _make_request(req_id: str, name: str = "Req") -> RequestData:
    return RequestData(id=req_id, name=name)


class TestLoadCandidates:
    def test_import_accepts_integer_or_string_mcp_param_type(self, tmp_path):
        request = _request_record(
            mcp_params={
                "sprint_id": {
                    "type": "integer_or_string",
                    "description": "Native integer or decimal string.",
                    "required": True,
                }
            }
        )
        path = _write(tmp_path, [_collection_record(requests=[request])])

        collections, parse_errors = load_collection_import_candidates(path)

        assert parse_errors == []
        assert collections[0].requests[0].mcp_params["sprint_id"].type == "integer_or_string"

    def test_happy_path_list_returns_both_collections(self, tmp_path):
        path = _write(
            tmp_path,
            [
                _collection_record(),
                _collection_record(id="col-2", name="Other API", requests=[]),
            ],
        )

        collections, parse_errors = load_collection_import_candidates(path)

        assert parse_errors == []
        assert [col.name for col in collections] == ["My API", "Other API"]
        assert all(isinstance(col, Collection) for col in collections)

    def test_preserves_every_request_field_needed_to_send_and_save(self, tmp_path):
        path = _write(tmp_path, [_collection_record()])

        collections, parse_errors = load_collection_import_candidates(path)

        assert parse_errors == []
        request = collections[0].requests[0]
        assert request.name == "List users"
        assert request.method == "POST"
        assert request.url == "https://api.example.com/users"
        assert request.headers == {"Authorization": "Bearer {{token}}"}
        assert request.params == {"page": "1"}
        assert request.body == '{"q": 1}'
        assert request.body_type == "json"
        assert request.post_script == "print(response.status_code)"
        assert request.expose_as_mcp is True
        assert request.mcp_description == "List all users"
        assert request.mcp_params["page"].type == "integer"
        assert request.mcp_params["page"].required is False

    def test_single_top_level_object_normalized_to_one_item(self, tmp_path):
        path = _write(tmp_path, _collection_record(name="Solo"))

        collections, parse_errors = load_collection_import_candidates(path)

        assert parse_errors == []
        assert len(collections) == 1
        assert collections[0].name == "Solo"

    def test_malformed_json_raises_file_error(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{not valid json", encoding="utf-8")

        with pytest.raises(CollectionImportFileError):
            load_collection_import_candidates(path)

    def test_missing_file_raises_file_error(self, tmp_path):
        with pytest.raises(CollectionImportFileError):
            load_collection_import_candidates(tmp_path / "nope.json")

    def test_scalar_json_root_raises_file_error(self, tmp_path):
        path = _write(tmp_path, "just a string")

        with pytest.raises(CollectionImportFileError):
            load_collection_import_candidates(path)

    def test_non_object_list_entry_raises_file_error(self, tmp_path):
        path = _write(tmp_path, [_collection_record(), "nope"])

        with pytest.raises(CollectionImportFileError):
            load_collection_import_candidates(path)

    def test_record_without_name_is_reported_not_silently_imported(self, tmp_path):
        path = _write(tmp_path, [{"info": {"schema": "postman"}, "item": []}])

        collections, parse_errors = load_collection_import_candidates(path)

        assert collections == []
        assert len(parse_errors) == 1
        assert "name" in parse_errors[0]

    def test_record_with_blank_name_is_reported(self, tmp_path):
        path = _write(tmp_path, [_collection_record(name="   ")])

        collections, parse_errors = load_collection_import_candidates(path)

        assert collections == []
        assert len(parse_errors) == 1

    def test_requests_not_a_list_is_reported_while_sibling_imports(self, tmp_path):
        path = _write(
            tmp_path,
            [
                _collection_record(id="col-bad", name="Broken", requests={"a": 1}),
                _collection_record(id="col-ok", name="Good", requests=[]),
            ],
        )

        collections, parse_errors = load_collection_import_candidates(path)

        assert [col.name for col in collections] == ["Good"]
        assert len(parse_errors) == 1
        assert "Broken" in parse_errors[0]

    def test_invalid_mcp_param_type_is_reported_while_sibling_imports(self, tmp_path):
        bad_request = _request_record(
            mcp_params={"page": {"type": "not-a-type", "description": "", "required": True}}
        )
        path = _write(
            tmp_path,
            [
                _collection_record(id="col-bad", name="Broken", requests=[bad_request]),
                _collection_record(id="col-ok", name="Good", requests=[]),
            ],
        )

        collections, parse_errors = load_collection_import_candidates(path)

        assert [col.name for col in collections] == ["Good"]
        assert len(parse_errors) == 1
        assert "Broken" in parse_errors[0]


class TestFindCollectionConflicts(unittest.TestCase):
    def test_returns_intersection_in_incoming_order_without_duplicates(self) -> None:
        existing = [_make_collection("c1", "My API"), _make_collection("c2", "Billing")]
        incoming = [
            _make_collection("i1", "New API"),
            _make_collection("i2", "Billing"),
            _make_collection("i3", "Billing"),
            _make_collection("i4", "My API"),
        ]

        self.assertEqual(
            find_collection_conflicts(existing, incoming), ["Billing", "My API"]
        )

    def test_no_conflicts_returns_empty_list(self) -> None:
        existing = [_make_collection("c1", "My API")]
        incoming = [_make_collection("i1", "New API")]

        self.assertEqual(find_collection_conflicts(existing, incoming), [])


class TestPlanOverwrite(unittest.TestCase):
    def test_preserves_existing_id_name_and_position(self) -> None:
        existing = [
            _make_collection("existing-a", "My API", [_make_request("old-req")]),
            _make_collection("existing-b", "Billing"),
        ]
        incoming = [_make_collection("incoming-a", "My API", [_make_request("new-req")])]

        result = plan_collection_import(
            existing, incoming, {"My API": ImportConflictDecision.OVERWRITE}
        )

        self.assertEqual(
            [col.id for col in result.collections], ["existing-a", "existing-b"]
        )
        updated = result.collections[0]
        self.assertEqual(updated.name, "My API")
        self.assertEqual([req.id for req in updated.requests], ["new-req"])
        self.assertEqual(result.updated, ["My API"])
        self.assertEqual([col.id for col in result.persisted], ["existing-a"])
        self.assertEqual(result.request_count, 1)

    def test_reimport_over_same_collection_keeps_request_ids(self) -> None:
        existing = [_make_collection("existing-a", "My API", [_make_request("req-1")])]
        incoming = [_make_collection("existing-a", "My API", [_make_request("req-1")])]

        result = plan_collection_import(
            existing, incoming, {"My API": ImportConflictDecision.OVERWRITE}
        )

        self.assertEqual([req.id for req in result.collections[0].requests], ["req-1"])


class TestPlanKeepBoth(unittest.TestCase):
    def test_appends_renamed_copy_and_leaves_existing_untouched(self) -> None:
        existing = [_make_collection("existing-a", "My API", [_make_request("old-req")])]
        incoming = [_make_collection("incoming-a", "My API", [_make_request("new-req")])]

        result = plan_collection_import(
            existing, incoming, {"My API": ImportConflictDecision.KEEP_BOTH}
        )

        self.assertEqual(len(result.collections), 2)
        untouched = result.collections[0]
        self.assertEqual(untouched.id, "existing-a")
        self.assertEqual([req.id for req in untouched.requests], ["old-req"])
        added = result.collections[1]
        self.assertEqual(added.name, "Copy of My API")
        self.assertEqual(result.renamed, [("My API", "Copy of My API")])
        self.assertEqual([col.name for col in result.persisted], ["Copy of My API"])

    def test_keep_both_uses_next_numbered_copy_when_copy_and_copy_2_taken(self) -> None:
        existing = [
            _make_collection("existing-a", "API"),
            _make_collection("existing-b", "Copy of API"),
            _make_collection("existing-c", "Copy of API (2)"),
        ]
        incoming = [_make_collection("incoming-a", "API")]

        result = plan_collection_import(
            existing, incoming, {"API": ImportConflictDecision.KEEP_BOTH}
        )

        self.assertEqual(
            [col.name for col in result.collections],
            ["API", "Copy of API", "Copy of API (2)", "Copy of API (3)"],
        )
        self.assertEqual(result.renamed, [("API", "Copy of API (3)")])
        self.assertEqual(
            [col.name for col in result.persisted],
            ["Copy of API (3)"],
        )
        self.assertEqual(
            [col.id for col in result.collections[:3]],
            ["existing-a", "existing-b", "existing-c"],
        )
        self.assertEqual(
            [col.name for col in result.collections[:3]],
            ["API", "Copy of API", "Copy of API (2)"],
        )


class TestPlanSkip(unittest.TestCase):
    def test_leaves_collections_identical_and_persists_nothing(self) -> None:
        existing = [_make_collection("existing-a", "My API", [_make_request("old-req")])]
        incoming = [_make_collection("incoming-a", "My API", [_make_request("new-req")])]

        result = plan_collection_import(
            existing, incoming, {"My API": ImportConflictDecision.SKIP}
        )

        self.assertEqual(len(result.collections), 1)
        self.assertEqual(result.collections[0].id, "existing-a")
        self.assertEqual([req.id for req in result.collections[0].requests], ["old-req"])
        self.assertEqual(result.skipped, ["My API"])
        self.assertEqual(result.persisted, [])


class TestPlanAdd(unittest.TestCase):
    def test_non_conflicting_name_always_added(self) -> None:
        existing = [_make_collection("existing-a", "My API")]
        incoming = [_make_collection("incoming-b", "Billing", [_make_request("r1")])]

        result = plan_collection_import(
            existing, incoming, {"SomeOtherName": ImportConflictDecision.SKIP}
        )

        self.assertEqual(result.added, ["Billing"])
        self.assertEqual(len(result.collections), 2)
        self.assertEqual(result.collections[1].id, "incoming-b")
        self.assertEqual(result.request_count, 1)


class TestPlanIdCollisions(unittest.TestCase):
    def test_colliding_collection_id_is_regenerated(self) -> None:
        existing = [_make_collection("shared-id", "My API")]
        incoming = [_make_collection("shared-id", "Billing")]

        result = plan_collection_import(existing, incoming, {})

        self.assertEqual(result.collections[0].id, "shared-id")
        self.assertNotEqual(result.collections[1].id, "shared-id")
        self.assertEqual(result.collections[1].name, "Billing")

    def test_colliding_request_id_is_regenerated(self) -> None:
        existing = [_make_collection("existing-a", "My API", [_make_request("shared-req")])]
        incoming = [_make_collection("incoming-b", "Billing", [_make_request("shared-req")])]

        result = plan_collection_import(existing, incoming, {})

        self.assertEqual(result.collections[0].requests[0].id, "shared-req")
        self.assertNotEqual(result.collections[1].requests[0].id, "shared-req")

    def test_free_ids_are_preserved(self) -> None:
        existing = [_make_collection("existing-a", "My API")]
        incoming = [_make_collection("incoming-b", "Billing", [_make_request("fresh-req")])]

        result = plan_collection_import(existing, incoming, {})

        self.assertEqual(result.collections[1].id, "incoming-b")
        self.assertEqual(result.collections[1].requests[0].id, "fresh-req")


class TestPlanDuplicateNamesWithinFile(unittest.TestCase):
    def test_second_duplicate_is_renamed_without_a_decision(self) -> None:
        existing: list[Collection] = []
        incoming = [
            _make_collection("i1", "Billing"),
            _make_collection("i2", "Billing"),
        ]

        result = plan_collection_import(existing, incoming, {})

        self.assertEqual(
            [col.name for col in result.collections], ["Billing", "Copy of Billing"]
        )
        self.assertEqual(result.added, ["Billing"])
        self.assertEqual(result.renamed, [("Billing", "Copy of Billing")])

    def test_three_duplicate_names_report_two_renames_each(self) -> None:
        existing: list[Collection] = []
        incoming = [
            _make_collection("i1", "API"),
            _make_collection("i2", "API"),
            _make_collection("i3", "API"),
        ]

        result = plan_collection_import(existing, incoming, {})

        self.assertEqual(
            [col.name for col in result.collections],
            ["API", "Copy of API", "Copy of API (2)"],
        )
        self.assertEqual(result.added, ["API"])
        self.assertEqual(
            result.renamed, [("API", "Copy of API"), ("API", "Copy of API (2)")]
        )
        self.assertEqual(len(result.renamed), 2)


class TestFormatResult(unittest.TestCase):
    def test_renders_counts_renames_and_errors(self) -> None:
        existing = [_make_collection("existing-a", "My API")]
        incoming = [_make_collection("incoming-a", "My API", [_make_request("r1")])]

        result = plan_collection_import(
            existing, incoming, {"My API": ImportConflictDecision.KEEP_BOTH}
        )
        result.parse_errors.append("Broken: missing name")
        summary = format_collection_import_result(result)

        self.assertIn("Copy of My API", summary)
        self.assertIn("Broken: missing name", summary)
        self.assertIn("1", summary)


class TestRecountCollectionImportPlan(unittest.TestCase):
    def test_recount_partial_addition_failure(self) -> None:
        self.assertIsNotNone(
            recount_collection_import_plan,
            "recount_collection_import_plan must be defined in pypost.core.collection_import",
        )
        existing: list[Collection] = []
        col1 = _make_collection("c1", "Added1", [_make_request("r1"), _make_request("r2")])
        col2 = _make_collection(
            "c2", "Added2", [_make_request("r3"), _make_request("r4"), _make_request("r5")]
        )
        plan = plan_collection_import(existing, [col1, col2], {})
        recounted = recount_collection_import_plan(plan, failed_ids={"c2"})

        self.assertEqual(recounted.added, ["Added1"])
        self.assertEqual(recounted.request_count, 2)
        self.assertEqual(recounted.updated, [])
        self.assertEqual(recounted.renamed, [])
        self.assertEqual(recounted.skipped, [])

    def test_recount_overwrite_failure(self) -> None:
        self.assertIsNotNone(
            recount_collection_import_plan,
            "recount_collection_import_plan must be defined in pypost.core.collection_import",
        )
        existing = [_make_collection("c1", "My API", [_make_request("old1")])]
        incoming = [
            _make_collection(
                "c1", "My API", [_make_request("n1"), _make_request("n2"), _make_request("n3")]
            )
        ]
        plan = plan_collection_import(
            existing, incoming, {"My API": ImportConflictDecision.OVERWRITE}
        )
        recounted = recount_collection_import_plan(plan, failed_ids={"c1"})

        self.assertEqual(recounted.updated, [])
        self.assertEqual(recounted.request_count, 0)
        self.assertEqual(recounted.added, [])

    def test_recount_renamed_copy_failure(self) -> None:
        self.assertIsNotNone(
            recount_collection_import_plan,
            "recount_collection_import_plan must be defined in pypost.core.collection_import",
        )
        existing = [_make_collection("c1", "My API", [_make_request("old1")])]
        incoming = [_make_collection("c2", "My API", [_make_request("n1")])]
        plan = plan_collection_import(
            existing, incoming, {"My API": ImportConflictDecision.KEEP_BOTH}
        )
        self.assertEqual(len(plan.persisted), 1)
        failed_id = plan.persisted[0].id
        recounted = recount_collection_import_plan(plan, failed_ids={failed_id})

        self.assertEqual(recounted.renamed, [])
        self.assertEqual(recounted.request_count, 0)
        self.assertEqual(recounted.added, [])

    def test_recount_total_failure_zeroes_all_counts(self) -> None:
        self.assertIsNotNone(
            recount_collection_import_plan,
            "recount_collection_import_plan must be defined in pypost.core.collection_import",
        )
        existing = [_make_collection("c1", "Existing")]
        col_new = _make_collection("c2", "New", [_make_request("r1")])
        col_up = _make_collection("c1", "Existing", [_make_request("r2")])
        plan = plan_collection_import(
            existing, [col_new, col_up], {"Existing": ImportConflictDecision.OVERWRITE}
        )
        all_failed = {col.id for col in plan.persisted}
        recounted = recount_collection_import_plan(plan, failed_ids=all_failed)

        self.assertEqual(recounted.added, [])
        self.assertEqual(recounted.updated, [])
        self.assertEqual(recounted.renamed, [])
        self.assertEqual(recounted.request_count, 0)

    def test_recount_happy_path_with_no_failures_preserves_plan(self) -> None:
        self.assertIsNotNone(
            recount_collection_import_plan,
            "recount_collection_import_plan must be defined in pypost.core.collection_import",
        )
        existing = [_make_collection("c1", "Existing")]
        col_new = _make_collection("c2", "New", [_make_request("r1")])
        plan = plan_collection_import(existing, [col_new], {})
        recounted = recount_collection_import_plan(plan, failed_ids=set())

        self.assertEqual(recounted.added, ["New"])
        self.assertEqual(recounted.request_count, 1)


if __name__ == "__main__":
    unittest.main()
