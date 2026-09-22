import unittest
from services.iso20022.iso_gateway import ISO20022Gateway

class TestISOGateway(unittest.TestCase):
    def test_pacs_008_generation(self):
        iso = ISO20022Gateway("TIMEIL01XXX")
        xml_msg = iso.generate_pacs_008_credit_transfer("Alice", "Bob", 15000.00, "USD")
        self.assertIn("pacs.008.001.10", xml_msg)
        self.assertIn("Alice", xml_msg)
        self.assertIn("15000.00", xml_msg)

if __name__ == "__main__":
    unittest.main()
