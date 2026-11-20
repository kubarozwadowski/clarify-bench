import copy
import unittest
from project_list import list_projects
class FinalChecks(unittest.TestCase):
    def test_order_and_ties(self):
        projects = [{"id":"z","name":"A","created_at":10},{"id":"b","name":"Z","created_at":20},{"id":"a","name":"Y","created_at":20},{"id":"c","name":"B","created_at":-1}]
        before = copy.deepcopy(projects)
        result = list_projects(projects)
        self.assertEqual([p["id"] for p in result],["a","b","z","c"])
        self.assertEqual(projects,before)
        self.assertIsNot(result,projects)
    def test_empty_and_singleton(self):
        self.assertEqual(list_projects([]),[])
        records = [{"id":"x","name":"X","created_at":0}]
        self.assertEqual(list_projects(records),records)
        self.assertIsNot(list_projects(records),records)
