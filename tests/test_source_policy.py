import unittest

from bridge.source_policy import PolicyError, decode_refresh_policy
from scripts.refresh_inventory import POLICY


class SourcePolicyTests(unittest.TestCase):
    def test_absent_and_exact_policy(self):
        self.assertIsNone(decode_refresh_policy(None))
        self.assertEqual(decode_refresh_policy(b'{"policy":"observed-inventory-v1"}'), POLICY)

    def test_rejects_invalid_marker(self):
        for data in (b'{"policy":true}', b'{"policy":"unknown"}',
                     b'{"policy":"observed-inventory-v1","policy":"observed-inventory-v1"}',
                     b'{"policy":"observed-inventory-v1","extra":0}', b'{}',
                     b'[]', b'null', b'\xff', b'{"policy":NaN}', b'{"policy":Infinity}'):
            with self.subTest(data=data), self.assertRaises(PolicyError):
                decode_refresh_policy(data)
