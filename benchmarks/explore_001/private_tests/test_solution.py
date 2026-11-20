import unittest
from handlers import get_user, get_team, get_project
class FinalChecks(unittest.TestCase):
    def test_found(self):
        project = {"name":"Research", "archived":False}
        self.assertEqual(get_project({"p7":project}, "p7"), (200, {"data":project}))
    def test_missing(self):
        for key in ("p7", "", 42):
            self.assertEqual(get_project({}, key), (404, {"error": {"code":"not_found", "resource":"project", "id":key}}))
    def test_falsy_record(self):
        self.assertEqual(get_project({"p0":{}}, "p0"), (200, {"data":{}}))
    def test_no_mutation(self):
        records = {"p1":{"name":"A"}}
        get_project(records, "p1")
        self.assertEqual(records, {"p1":{"name":"A"}})
    def test_preserve_existing(self):
        for handler, resource in ((get_user,"user"),(get_team,"team")):
            self.assertEqual(handler({}, "x"), (404, {"error": {"code":"not_found", "resource":resource, "id":"x"}}))
            self.assertEqual(handler({"x":1}, "x"), (200, {"data":1}))
