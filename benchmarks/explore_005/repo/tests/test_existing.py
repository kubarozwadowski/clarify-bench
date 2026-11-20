import unittest
from lookups import find_invoice, find_note
class ExistingBehavior(unittest.TestCase):
    def test_invoice_scope(self):
        records = [{"id":"i1","tenant_id":"a"},{"id":"i1","tenant_id":"b"}]
        self.assertIs(find_invoice(records,"b","i1"),records[1])
    def test_note_missing(self):
        self.assertIsNone(find_note([{"id":"n1","tenant_id":"a"}],"b","n1"))
