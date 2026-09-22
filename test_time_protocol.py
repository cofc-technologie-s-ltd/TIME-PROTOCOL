import unittest
import asyncio
from time_ledger import SecureTimeLedger
from time_crypto import PostQuantumSigner
from cash_adapter import CashProtocolAdapter
from time_websocket import WebSocketConnectionManager

class TestTimeProtocolCore(unittest.TestCase):
    def setUp(self):
        self.ledger = SecureTimeLedger()
        self.secret_key = "TIME_TEST_KEY_2026"
        self.master_wallet = "bc1q3cmhzwxa35egpqhr5eddrqqfmdd8jyeqqkky6h"

    def test_ledger_nonce_protection(self):
        success1 = self.ledger.update_account(self.master_wallet, balance=1000, nonce=1, staked=500)
        self.assertTrue(success1)

        success_replay = self.ledger.update_account(self.master_wallet, balance=2000, nonce=1, staked=500)
        self.assertFalse(success_replay)

        success2 = self.ledger.update_account(self.master_wallet, balance=1500, nonce=2, staked=500)
        self.assertTrue(success2)

    def test_post_quantum_signature(self):
        payload = {"account": self.master_wallet, "amount": 500}
        signature = PostQuantumSigner.sign_payload(payload, self.secret_key)
        
        valid = PostQuantumSigner.verify_payload(payload, signature, self.secret_key)
        self.assertTrue(valid)

        tampered_payload = {"account": self.master_wallet, "amount": 9999}
        invalid = PostQuantumSigner.verify_payload(tampered_payload, signature, self.secret_key)
        self.assertFalse(invalid)

    def test_cash_protocol_interop(self):
        adapter = CashProtocolAdapter(self.secret_key)
        wrapped = adapter.wrap_cash_transfer(self.master_wallet, "TIME_RECIPIENT_TEST", 100, nonce=1)
        self.assertTrue(adapter.verify_cash_transfer(wrapped))

    def test_websocket_manager_initialization(self):
        ws_mgr = WebSocketConnectionManager()
        self.assertEqual(len(ws_mgr.active_connections), 0)

if __name__ == "__main__":
    unittest.main()
