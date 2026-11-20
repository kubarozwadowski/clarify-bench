import unittest
from settings import resolve_port, resolve_workers
class ExistingBehavior(unittest.TestCase):
    def test_port_precedence(self):
        self.assertEqual(resolve_port({"port":9000},{"port":8000},{"port":7000}),9000)
        self.assertEqual(resolve_port({}, {"port":8000},{"port":7000}),8000)
    def test_defaults_and_zero(self):
        self.assertEqual(resolve_port({}, {}, {}),8080)
        self.assertEqual(resolve_workers({"workers":0},{"workers":2},{}),0)
        self.assertEqual(resolve_workers({}, {}, {}),4)
