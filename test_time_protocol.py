import unittest
from time_ledger import SecureTimeLedger
from time_crypto import PostQuantumSigner
from cash_adapter import CashProtocolAdapter

class TestTimeProtocolCore(unittest.TestCase):
    def setUp(self):
        self.ledger = SecureTimeLedger()
        self.secret_key = "TIME_TEST_KEY_2026"
        self.master_wallet = "bc1q3cmhzwxa35egpqhr5eddrqqfmdd8jyeqqkky6h"

    def test_ledger_nonce_protection(self):
        # Initial update
        success1 = self.ledger.update_account(self.master_wallet, balance=1000, nonce=1, staked=500)
        self.assertTrue(success1)

        # Replay attack with same nonce should fail
        success_replay = self.ledger.update_account(self.master_wallet, balance=2000, nonce=1, staked=500)
        self.assertFalse(success_replay)

        # Valid monotonic nonce increment
        success2 = self.ledger.update_account(self.master_wallet, balance=1500, nonce=2, staked=500)
        self.assertTrue(success2)

    def test_post_quantum_signature(self):
        payload = {"account": self.master_wallet, "amount": 500}
        signature = PostQuantumSigner.sign_payload(payload, self.secret_key)
        
        valid = PostQuantumSigner.verify_payload(payload, signature, self.secret_key)
        self.assertTrue(valid)

        # Tampered payload check
        tampered_payload = {"account": self.master_wallet, "amount": 9999}
        invalid = PostQuantumSigner.verify_payload(tampered_payload, signature, self.secret_key)
        self.assertFalse(invalid)

    def test_cash_protocol_interop(self):
        adapter = CashProtocolAdapter(self.secret_key)
        wrapped = adapter.wrap_cash_transfer(self.master_wallet, "TIME_RECIPIENT_TEST", 100, nonce=1)
        self.assertTrue(adapter.verify_cash_transfer(wrapped))

if __name__ == "__main__":
    unittest.main()
