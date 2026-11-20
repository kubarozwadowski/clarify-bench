import copy
import unittest
from redaction import redact_record
class FinalChecks(unittest.TestCase):
    def test_each_sensitive_key_even_falsy(self):
        for key in ("password","api_key","access_token"):
            for value in ("example",None,"",0,False):
                with self.subTest(key=key,value=value):
                    record = {key:value,"name":"Ada"}
                    before = record.copy()
                    result = redact_record(record)
                    self.assertEqual(result,{key:"[REDACTED]","name":"Ada"})
                    self.assertEqual(record,before)
                    self.assertIsNot(result,record)
    def test_exact_keys_and_shallow_copy(self):
        nested = {"password":"keep-nested"}
        record = {"password":"a","api_key":"b","access_token":"c","Password":"keep","password_hint":"keep","nested":nested}
        before = copy.deepcopy(record)
        result = redact_record(record)
        self.assertEqual(result,{"password":"[REDACTED]","api_key":"[REDACTED]","access_token":"[REDACTED]","Password":"keep","password_hint":"keep","nested":nested})
        self.assertIs(result["nested"],nested)
        self.assertEqual(record,before)
    def test_empty_is_new_dict(self):
        record = {}
        result = redact_record(record)
        self.assertEqual(result,{})
        self.assertIsNot(result,record)
