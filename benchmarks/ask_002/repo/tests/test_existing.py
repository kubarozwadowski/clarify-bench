import copy
import unittest
from project_list import list_projects
class SmokeChecks(unittest.TestCase):
    def test_membership_and_no_mutation(self):
        projects = [{"id":"p1","name":"One","created_at":10},{"id":"p2","name":"Two","created_at":20}]
        before = copy.deepcopy(projects)
        result = list_projects(projects)
        self.assertIsInstance(result,list)
        self.assertIsNot(result,projects)
        self.assertCountEqual(result,projects)
        self.assertEqual(projects,before)
