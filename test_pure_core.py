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

    def test_nasdaq_spac_bridge(self):
        from nasdaq_spac_bridge import NasdaqSpacBridge
        bridge = NasdaqSpacBridge("TIME_TEST_KEY_2026", "COFC Technologies LTD")
        
        # Test FIX Protocol encoding for NASDAQ/Exchange routing
        fix_fields = {"11": "ORD_2026_001", "54": "1", "55": "TIME/USD", "38": "10000", "40": "2"}
        fix_msg = bridge.encode_fix_message("D", "COFC_NODE", "NASDAQ_EXCHANGE", fix_fields)
        self.assertIn("FIX.4.4", fix_msg)
        self.assertIn("35=D", fix_msg)
        self.assertIn("1001=", fix_msg)

        # Test Smart SPAC Tokenization wrapper
        spac_data = bridge.create_spac_token_wrapper("COFC-TIME", 1000000000, 5000000)
        self.assertEqual(spac_data["spac_packet"]["symbol"], "COFC-TIME")
        self.assertTrue(len(spac_data["digital_seal"]) > 0)

    def test_global_asset_gateway(self):
        from global_asset_gateway import GlobalAssetGateway
        gateway = GlobalAssetGateway("TIME_TEST_KEY_2026")
        
        # Register global assets (Fiat USD, Gold, Bitcoin)
        gateway.register_asset("USD", "FIAT", "Federal Reserve / Sovereign Bridge")
        gateway.register_asset("XAU", "COMMODITY", "COFC Dark Vault Sovereign Gold")
        gateway.register_asset("BTC", "CRYPTO", "Decentralized Network Bridge")
        
        # Execute cross-border settlement in USD
        res_usd = gateway.execute_cross_border_settlement("ACC_SENDER_01", "ACC_RECEIVER_02", "USD", 1500000.50)
        self.assertEqual(res_usd["status"], "SETTLED_INSTANT")
        self.assertEqual(res_usd["iso_20022_payload"]["amount"], 1500000.50)
        self.assertTrue(len(res_usd["cryptographic_seal"]) > 0)

        # Execute settlement in Gold (XAU)
        res_xau = gateway.execute_cross_border_settlement("ACC_VAULT_01", "ACC_GLOBAL_03", "XAU", 250.75)
        self.assertEqual(res_xau["iso_20022_payload"]["asset_class"], "COMMODITY")
