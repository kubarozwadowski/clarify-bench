import copy
import unittest
from listings import list_teams
class FinalChecks(unittest.TestCase):
    def test_visibility_and_input_preservation(self):
        teams = [{"id":"a"},{"id":"b","deleted_at":None},{"id":"c","deleted_at":"2026-01-01"},{"id":"d","deleted_at":""},{"id":"e","deleted_at":0},{"id":"f","deleted_at":False}]
        before = copy.deepcopy(teams)
        result = list_teams(teams)
        self.assertEqual(result,teams[:2])
        self.assertIsNot(result,teams)
        self.assertIs(result[0],teams[0])
        self.assertIs(result[1],teams[1])
        self.assertEqual(teams,before)
    def test_empty_and_all_deleted(self):
        teams = []
        result = list_teams(teams)
        self.assertEqual(result,[])
        self.assertIsNot(result,teams)
        self.assertEqual(list_teams([{"deleted_at":1}]),[])
