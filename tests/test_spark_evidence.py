"""Independent parity checks; these tests do not require Java or PySpark."""
import unittest

from backend.spark_job import compare_aggregates


class SparkEvidenceTests(unittest.TestCase):
    def test_same_city_month_values_pass_with_float_tolerance(self):
        expected = [{"city": "Hyderabad", "month": "2025-01", "records": 2,
                     "temperature": 25., "precipitation": 3., "humidity": 55., "wind_speed": 8.}]
        actual = [dict(expected[0], temperature=25.00000000001)]
        self.assertTrue(compare_aggregates(actual, expected)["passed"])

    def test_missing_month_and_wrong_rainfall_fail(self):
        row = {"city": "Delhi", "month": "2025-01", "records": 2,
               "temperature": 20., "precipitation": 4., "humidity": 60., "wind_speed": 7.}
        self.assertFalse(compare_aggregates([], [row])["passed"])
        self.assertFalse(compare_aggregates([dict(row, precipitation=8.)], [row])["passed"])

    def test_duplicate_month_or_nan_must_not_verify(self):
        row = {"city": "Delhi", "month": "2025-01", "records": 1,
               "temperature": 20., "precipitation": 0., "humidity": 60., "wind_speed": 7.}
        self.assertFalse(compare_aggregates([row, row], [row])["passed"])
        self.assertFalse(compare_aggregates([dict(row, temperature=float("nan"))], [row])["passed"])


if __name__ == "__main__":
    unittest.main()
