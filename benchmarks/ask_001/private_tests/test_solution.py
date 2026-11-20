import copy
import unittest
from projects import delete_project
class FinalChecks(unittest.TestCase):
    def test_retention(self):
        state = {"projects":{"p1":{"name":"One"},"p2":{"name":"Two"}}, "uploads":{"u1":{"project_id":"p1","name":"a.txt"},"u2":{"project_id":"p2","name":"b.txt"}}}
        original_uploads = copy.deepcopy(state["uploads"])
        self.assertIs(delete_project(state, "p1"), True)
        self.assertEqual(state["projects"], {"p2":{"name":"Two"}})
        self.assertEqual(state["uploads"], original_uploads)
    def test_missing_no_change(self):
        state = {"projects":{}, "uploads":{"u1":{"project_id":"p0"}}}
        before = copy.deepcopy(state)
        self.assertIs(delete_project(state, "p0"), False)
        self.assertEqual(state, before)
    def test_repeat(self):
        state = {"projects":{"p1":{}}, "uploads":{}}
        self.assertIs(delete_project(state, "p1"), True)
        self.assertIs(delete_project(state, "p1"), False)
