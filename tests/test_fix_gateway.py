import unittest
from services.gateway.fix_gateway import FIXGateway

class TestFIXGateway(unittest.TestCase):
    def test_fix_order_processing(self):
        gateway = FIXGateway()
        parsed = gateway.parse_fix_message("8=FIX.4.4|35=D|56=TARGET")
        self.assertEqual(parsed["status"], "parsed")
        
        exec_report = gateway.create_order_execution_report("ORD-1001", "FILLED", 500.0)
        self.assertEqual(exec_report["MsgType"], "8")
        self.assertEqual(exec_report["OrderID"], "ORD-1001")

if __name__ == "__main__":
    unittest.main()
