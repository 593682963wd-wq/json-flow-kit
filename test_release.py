"""作者：Wangyuan；日期：2026-11-08。职责：验证JSON字段保留、结构去重与Markdown转义。"""
import unittest
from transforms import _resolve_path, _dedupe_rows, _to_markdown


class TransformRegressions(unittest.TestCase):
    def test_filter_requires_present_key(self) -> None:
        self.assertEqual(_resolve_path({"items": [{"v": 1}, {"k": "None", "v": 2}]}, "items[k=None].v"), 2)

    def test_dedupe_ignores_object_insertion_order(self) -> None:
        self.assertEqual(len(_dedupe_rows([{"a": 1, "b": 2}, {"b": 2, "a": 1}], None)), 1)

    def test_dedupe_accepts_json_container_key(self) -> None:
        self.assertEqual(len(_dedupe_rows([{"k": [1]}, {"k": [1]}], "k")), 1)

    def test_markdown_keeps_union_of_headers_and_escapes_cells(self) -> None:
        result = _to_markdown([{"a": 1}, {"a": "b|c\nd", "b": 3}])
        self.assertIn("| a | b |", result)
        self.assertIn("b\\|c<br>d", result)
        self.assertIn("3", result)
