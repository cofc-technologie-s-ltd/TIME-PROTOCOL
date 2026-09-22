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

    def test_liquidity_router(self):
        from liquidity_router import LiquidityRouter
        router = LiquidityRouter("TIME_TEST_KEY_2026")
        
        # Submit buy order
        buy_res = router.submit_order("TIME/USD", "BUY", 125.50, 1000.0, "TRADER_ALFA")
        self.assertEqual(buy_res["status"], "ORDER_PROCESSED")
        self.assertFalse(buy_res["execution"]["matched"])

        # Submit matching sell order
        sell_res = router.submit_order("TIME/USD", "SELL", 125.50, 500.0, "TRADER_BETA")
        self.assertTrue(sell_res["execution"]["matched"])
        self.assertEqual(sell_res["execution"]["executed_price"], 125.50)
        self.assertEqual(sell_res["execution"]["executed_quantity"], 500.0)

    def test_telemetry_monitor(self):
        from telemetry_monitor import SystemTelemetryMonitor
        monitor = SystemTelemetryMonitor("VALIDATOR_NODE_01")
        
        # Record performance metrics
        metric = monitor.record_metric("throughput_tps", 544220.0, "TX/sec")
        self.assertEqual(metric["value"], 544220.0)

        # Trigger security alert test
        alert = monitor.trigger_security_alert("HIGH", "NONCE_MISMATCH", "Potential replay attempt detected.")
        self.assertEqual(alert["severity"], "HIGH")

        # Generate health report
        report = monitor.generate_health_report()
        self.assertEqual(report["status"], "HEALTHY")
        self.assertEqual(report["total_security_alerts"], 1)

    def test_p2p_network(self):
        from p2p_network import P2PNetworkNode
        node_a = P2PNetworkNode("VALIDATOR_A", "127.0.0.1", 9001)
        node_b = P2PNetworkNode("VALIDATOR_B", "127.0.0.1", 9002)

        # Connect peer
        connected = node_a.connect_peer(node_b.node_id, node_b.host, node_b.port)
        self.assertTrue(connected)
        self.assertEqual(node_a.get_network_topology()["peer_count"], 1)

        # Broadcast gossip message
        broadcast_res = node_a.broadcast_gossip("BLOCK_COMMIT", {"block_height": 1001, "hash": "0xabc123"})
        self.assertEqual(broadcast_res["status"], "BROADCAST_SUCCESS")
        self.assertEqual(broadcast_res["active_peers_reached"], 1)

    def test_sovereign_mainnet_node(self):
        from mainnet_node import SovereignMainnetNode
        node = SovereignMainnetNode("ROOT_VALIDATOR_01", "127.0.0.1", 8080)
        
        # Start node
        start_res = node.start_node()
        self.assertEqual(start_res["status"], "ONLINE")

        # Process transaction through node
        success = node.process_sovereign_transaction("bc1q3cmhzwxa35egpqhr5eddrqqfmdd8jyeqqkky6h", 1000, 1, 500)
        self.assertTrue(success)

        # Stop node
        stop_res = node.stop_node()
        self.assertEqual(stop_res["status"], "SHUTDOWN")

    def test_time_cli_operations(self):
        from mainnet_node import SovereignMainnetNode
        node = SovereignMainnetNode("CLI_TEST_NODE", "127.0.0.1", 9090)
        node.start_node()
        
        # Verify transaction pipeline via node simulation
        res = node.process_sovereign_transaction("bc1q_test_cli_address", 5000, 1, 2500)
        self.assertTrue(res)
        
        # Verify telemetry recording
        node.telemetry.record_metric("cli_health", 1.0, "OPTIMAL")
        self.assertIn("cli_health", node.telemetry.metrics)
        
        node.stop_node()

    def test_institutional_fix_bridge(self):
        from nasdaq_spac_bridge import InstitutionalFIXBridge
        bridge = InstitutionalFIXBridge("TEST_SENDER", "TEST_TARGET")
        
        # Test FIX message generation
        msg = bridge.generate_fix_message("D", {"55": "BTC/USD", "54": "1", "38": "100"})
        self.assertIn("8=FIX.4.4", msg)
        self.assertIn("35=D", msg)
        
        # Test execution gateway routing
        result = bridge.execute_order("TIME/BTC", "BUY", 500, 0.0015)
        self.assertEqual(result["status"], "TRANSMITTED_TO_EXCHANGE")
        self.assertIn("10=", result["fix_packet"])
        self.assertTrue(bridge.active_session)
