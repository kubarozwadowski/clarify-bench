import unittest
from projects import delete_project
class SmokeChecks(unittest.TestCase):
    def test_missing_empty_state(self):
        state = {"projects":{}, "uploads":{}}
        self.assertFalse(delete_project(state, "missing"))
        self.assertEqual(state, {"projects":{}, "uploads":{}})
