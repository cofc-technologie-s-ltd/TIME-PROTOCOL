import unittest
import os
import json
from time_ledger import SecureTimeLedger
from time_crypto import PostQuantumSigner
from cash_adapter import CashProtocolAdapter
from universal_bridge import UniversalExchangeWalletBridge
from time_consensus import TimeConsensusManager
from time_cluster import TimeClusterOrchestrator

class TestPureCoreProtocol(unittest.TestCase):
    def setUp(self):
        self.ledger = SecureTimeLedger()
        self.secret_key = "TIME_TEST_KEY_2026"
        self.master_wallet = "bc1q3cmhzwxa35egpqhr5eddrqqfmdd8jyeqqkky6h"
        self.bridge = UniversalExchangeWalletBridge(self.secret_key)
        self.cash_adapter = CashProtocolAdapter(self.secret_key)

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

    def test_cash_protocol_interop(self):
        wrapped = self.cash_adapter.wrap_cash_transfer(self.master_wallet, "TIME_RECIPIENT_TEST", 100, nonce=1)
        self.assertTrue(self.cash_adapter.verify_cash_transfer(wrapped))

    def test_universal_exchange_wallet_bridge(self):
        coinex_payload = {"address": self.master_wallet, "amount": 5000, "tx_id_int": 102}
        res = self.bridge.parse_exchange_withdrawal("CoinEx", coinex_payload)
        self.assertEqual(res["normalized_packet"]["source_exchange"], "COINEX")
        self.assertTrue(PostQuantumSigner.verify_payload(res["normalized_packet"], res["signature"], self.secret_key))

    def test_cluster_orchestrator(self):
        orchestrator = TimeClusterOrchestrator(node_count=3)
        status = orchestrator.get_cluster_status()
        self.assertEqual(status["active_nodes"], 3)
        self.assertTrue(orchestrator.nodes[0].process_transaction(self.master_wallet, 500, 1, 100))

if __name__ == "__main__":
    unittest.main()
