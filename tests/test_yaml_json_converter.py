import pytest

import unittest

from pypost.core.yaml_json_converter import (
    YamlBodyConversionError,
    convert_json_object_to_yaml,
    convert_yaml_body_to_object,
)

pytestmark = pytest.mark.timeout(30)


class TestConvertYamlBodyToObject(unittest.TestCase):
    def test_valid_mapping(self):
        result = convert_yaml_body_to_object("key: value\nnum: 42")
        self.assertEqual({"key": "value", "num": 42}, result)

    def test_valid_list(self):
        result = convert_yaml_body_to_object("- a\n- b\n- c")
        self.assertEqual(["a", "b", "c"], result)

    def test_nested_structure(self):
        yaml_text = "user:\n  name: Alice\n  roles:\n    - admin\n    - user"
        result = convert_yaml_body_to_object(yaml_text)
        self.assertEqual(
            {"user": {"name": "Alice", "roles": ["admin", "user"]}},
            result,
        )

    def test_invalid_yaml_raises(self):
        with self.assertRaises(YamlBodyConversionError):
            convert_yaml_body_to_object("{ invalid yaml")

    def test_multi_document_raises(self):
        text = "key: first\n---\nkey: second"
        with self.assertRaises(YamlBodyConversionError) as ctx:
            convert_yaml_body_to_object(text)
        self.assertIn("Expected exactly one YAML document", str(ctx.exception))

    def test_empty_body_raises(self):
        with self.assertRaises(YamlBodyConversionError):
            convert_yaml_body_to_object("   ")

    def test_null_document_raises(self):
        with self.assertRaises(YamlBodyConversionError):
            convert_yaml_body_to_object("---")

    def test_non_json_serializable_raises(self):
        with self.assertRaises(YamlBodyConversionError) as ctx:
            convert_yaml_body_to_object("dt: 2020-01-01T12:00:00")
        self.assertIn("not JSON-serializable", str(ctx.exception))


class TestConvertJsonObjectToYaml(unittest.TestCase):
    def test_mapping(self):
        result = convert_json_object_to_yaml({"key": "value", "num": 42})
        self.assertEqual(convert_yaml_body_to_object(result), {"key": "value", "num": 42})

    def test_list(self):
        result = convert_json_object_to_yaml(["a", "b", "c"])
        self.assertEqual(convert_yaml_body_to_object(result), ["a", "b", "c"])

    def test_nested_structure(self):
        obj = {"user": {"name": "Alice", "roles": ["admin", "user"]}}
        result = convert_json_object_to_yaml(obj)
        self.assertEqual(convert_yaml_body_to_object(result), obj)


if __name__ == "__main__":
    unittest.main()
