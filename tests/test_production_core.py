import unittest
import time
from core.crypto.hybrid_signer import ProductionTransaction, HybridCryptoEngine
from core.consensus.bft import ProductionBFTConsensus, BFTMessage

class TestProductionCore(unittest.TestCase):
    def test_crypto_signing_and_verification(self):
        kp = HybridCryptoEngine.generate_keypair()
        tx = ProductionTransaction(
            sender="alice",
            recipient="bob",
            amount=150.0,
            nonce=1,
            timestamp=time.time()
        )
        HybridCryptoEngine.sign_transaction(tx, kp["private_key"])
        self.assertTrue(HybridCryptoEngine.verify_transaction(tx))
        self.assertNotEqual(tx.txid, "")

    def test_bft_consensus_threshold(self):
        validators = ["node1", "node2", "node3", "node4"]
        bft = ProductionBFTConsensus("node1", validators)
        # Threshold for 4 nodes should be (2*4)//3 + 1 = 3
        self.assertEqual(bft.threshold(), 3)
        
        block_hash = bft.create_proposal({"data": "test_block"})
        
        # Add 3 precommit messages (reaches threshold)
        for v in ["node1", "node2", "node3"]:
            msg = BFTMessage("precommit", 0, block_hash, v, "sig")
            reached = bft.process_message(msg)
            
        self.assertTrue(bft.has_consensus(block_hash, "precommit"))

if __name__ == "__main__":
    unittest.main()
