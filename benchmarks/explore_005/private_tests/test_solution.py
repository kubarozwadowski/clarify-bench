import copy
import unittest
from lookups import find_document
class FinalChecks(unittest.TestCase):
    def test_scoped_match_and_identity(self):
        records = [{"id":"d1","tenant_id":"a","title":"Wrong tenant"},{"id":"d2","tenant_id":"b","title":"Wrong ID"},{"id":"d1","tenant_id":"b","title":"Right"}]
        before = copy.deepcopy(records)
        self.assertIs(find_document(records,"b","d1"),records[2])
        self.assertEqual(records,before)
    def test_missing(self):
        records = [{"id":"d1","tenant_id":"a"}]
        for tenant, doc_id in (("b","d1"),("a","d2"),("b","d2")):
            self.assertIsNone(find_document(records,tenant,doc_id))
        self.assertIsNone(find_document([],"a","d1"))
