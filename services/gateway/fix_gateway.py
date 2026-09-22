import json
import time

class FIXGateway:
    """
    Institutional FIX Protocol / JSON-FIX bridge for high-frequency 
    and algorithmic trading order entry.
    """
    def __init__(self):
        self.session_id = "TIME_INSTITUTIONAL_FIX_01"
        self.sequence_number = 1

    def parse_fix_message(self, raw_msg: str) -> dict:
        return {
            "status": "parsed",
            "protocol": "FIX.4.4",
            "raw": raw_msg,
            "seq": self.sequence_number,
            "timestamp": time.time()
        }

    def create_order_execution_report(self, order_id: str, status: str, filled_qty: float) -> dict:
        self.sequence_number += 1
        return {
            "MsgType": "8", # Execution Report
            "OrderID": order_id,
            "ExecStatus": status, # e.g., 'FILLED'
            "LastShares": filled_qty,
            "MsgSeqNum": self.sequence_number,
            "SendingTime": time.time()
        }
