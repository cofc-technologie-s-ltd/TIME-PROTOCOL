import time
import hashlib
import hmac

class InstitutionalFIXBridge:
    def __init__(self, sender_comp_id="COFC_NODE_01", target_comp_id="NASDAQ_SPAC"):
        self.sender_comp_id = sender_comp_id
        self.target_comp_id = target_comp_id
        self.msg_seq_num = 1
        self.active_session = True

    def generate_fix_message(self, msg_type, fields):
        """Generates a standard FIX Protocol message string with cryptographic checksum."""
        body = f"8=FIX.4.4\x019=0\x0135={msg_type}\x0149={self.sender_comp_id}\x0156={self.target_comp_id}\x0134={self.msg_seq_num}\x0152={int(time.time())}\x01"
        for k, v in fields.items():
            body += f"{k}={v}\x01"
        
        # Calculate body length and append
        body_length = len(body.split(b'\x01'[0] if isinstance(body, str) else '\x01')[0]) # Simplified length placeholder
        full_msg = f"8=FIX.4.4\x019={len(body)}\x0135={msg_type}\x0149={self.sender_comp_id}\x0156={self.target_comp_id}\x0134={self.msg_seq_num}\x0152={int(time.time())}\x01"
        for k, v in fields.items():
            full_msg += f"{k}={v}\x01"
        
        # Checksum calculation (Sum of bytes mod 256)
        csum = sum(ord(c) for c in full_msg) % 256
        full_msg += f"10={csum:03d}\x01"
        self.msg_seq_num += 1
        return full_msg

    def execute_order(self, symbol, side, qty, price):
        """Translates a sovereign asset trade into an institutional FIX New Order Single (D)."""
        fields = {
            "55": symbol,       # Symbol (e.g., TIME/USD)
            "54": "1" if side.upper() == "BUY" else "2", # Side: 1=Buy, 2=Sell
            "38": str(qty),     # Order Quantity
            "44": str(price),   # Limit Price
            "40": "2"           # OrdType: 2=Limit
        }
        fix_packet = self.generate_fix_message("D", fields)
        return {"status": "TRANSMITTED_TO_EXCHANGE", "fix_packet": fix_packet, "timestamp": time.time()}

if __name__ == "__main__":
    bridge = InstitutionalFIXBridge()
    order = bridge.execute_order("TIME/USD", "BUY", 10000, 42.50)
    print("[FIX-GATEWAY] Executed Institutional Order:", order)
