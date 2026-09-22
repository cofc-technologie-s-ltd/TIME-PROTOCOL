import time

class ProductionFIXGateway:
    def __init__(self):
        self.session_id = "COFC_FIX_PRODUCTION"
        self.seq_num = 1

    def parse_order(self, raw: str) -> dict:
        return {"status": "parsed", "protocol": "FIX.4.4", "raw": raw, "seq": self.seq_num, "time": time.time()}

    def execution_report(self, order_id: str, qty: float) -> dict:
        self.seq_num += 1
        return {"MsgType": "8", "OrderID": order_id, "Status": "FILLED", "Qty": qty, "Seq": self.seq_num}
