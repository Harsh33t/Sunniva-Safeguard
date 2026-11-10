import os
import tempfile
import unittest

from real_tools import GLOBAL_MEMORY, execute_python_code


class SafePythonToolTests(unittest.TestCase):
    def setUp(self):
        GLOBAL_MEMORY.clear()

    def tearDown(self):
        GLOBAL_MEMORY.clear()

    def test_calculations_and_output_run_in_restricted_interpreter(self):
        result = execute_python_code("total = sum([2, 3, 5])\nprint(total)\nresult = round(total / 3, 2)")

        self.assertEqual(result, {"success": True, "stdout": "10", "stderr": "", "return_value": "3.33"})

    def test_memory_operations_are_explicit_and_work_across_calls(self):
        written = execute_python_code('memory_set("review-count", 4)\nresult = memory_get("review-count")')
        read = execute_python_code('result = memory_get("review-count", 0) + 1')

        self.assertTrue(written["success"])
        self.assertEqual(written["return_value"], "4")
        self.assertEqual(read["return_value"], "5")

    def test_rejects_import_attribute_access_and_arbitrary_statements(self):
        forbidden = [
            "import os",
            "result = __import__('os').getcwd()",
            "result = ().__class__.__mro__",
            "while True: pass",
            "result = [x for x in [1, 2]]",
        ]

        for snippet in forbidden:
            with self.subTest(snippet=snippet):
                result = execute_python_code(snippet)
                self.assertFalse(result["success"])
                self.assertRegex(result["stderr"].lower(), r"not supported|not permitted")

    def test_rejected_code_cannot_create_a_file(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = os.path.join(directory, "executed")
            snippet = f"open({marker!r}, 'w').write('bad')"

            result = execute_python_code(snippet)

            self.assertFalse(result["success"])
            self.assertFalse(os.path.exists(marker))

    def test_resource_limits_reject_large_repetition_and_exponents(self):
        for snippet in ("result = [0] * 100000000", "result = 2 ** 100000000"):
            with self.subTest(snippet=snippet):
                result = execute_python_code(snippet)
                self.assertFalse(result["success"])
                self.assertIn("safe", result["stderr"].lower())

    def test_source_and_printed_output_limits_are_enforced(self):
        oversized_source = execute_python_code("#" + ("x" * 8_000))
        oversized_output = execute_python_code("\n".join(['print("x" * 900)'] * 19))

        self.assertFalse(oversized_source["success"])
        self.assertIn("character limit", oversized_source["stderr"].lower())
        self.assertFalse(oversized_output["success"])
        self.assertIn("output exceeds", oversized_output["stderr"].lower())

    def test_shared_memory_changes_are_rolled_back_when_later_code_is_rejected(self):
        result = execute_python_code('memory_set("partial", "not committed")\nprint([1] * 100000)')

        self.assertFalse(result["success"])
        self.assertIsNone(GLOBAL_MEMORY.get("partial"))

    def test_legacy_substring_filter_bypass_is_no_longer_relevant(self):
        result = execute_python_code("result = sum([1, 2, 3]) # subprocess is mentioned as harmless text")

        self.assertTrue(result["success"])
        self.assertEqual(result["return_value"], "6")


if __name__ == "__main__":
    unittest.main()
