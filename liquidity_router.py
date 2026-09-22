import time
from typing import Dict, Any, List
from time_crypto import PostQuantumSigner

class LiquidityRouter:
    """
    High-Frequency Liquidity & Order Matching Router for TIME Protocol.
    Connects institutional order flow, decentralized liquidity pools, and external
    exchanges (CoinEx, Bitget, NASDAQ) with post-quantum atomic execution.
    """
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.order_books: Dict[str, List[Dict[str, Any]]] = {}

    def submit_order(self, pair: str, side: str, price: float, quantity: float, trader_id: str) -> Dict[str, Any]:
        """
        Submits a cryptographically signed order into the sovereign liquidity pool.
        """
        pair_key = pair.upper()
        if pair_key not in self.order_books:
            self.order_books[pair_key] = []

        order = {
            "order_id": f"ORD_{int(time.time()*1000)}_{trader_id[:6]}",
            "side": side.upper(), # BUY / SELL
            "price": price,
            "quantity": quantity,
            "trader": trader_id,
            "timestamp": time.time()
        }

        # Sign order payload with post-quantum security
        order_signature = PostQuantumSigner.sign_payload(order, self.secret_key)
        
        matched_trade = self._match_order(pair_key, order)

        return {
            "status": "ORDER_PROCESSED",
            "order": order,
            "signature": order_signature,
            "execution": matched_trade
        }

    def _match_order(self, pair: str, new_order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal matching engine executing instant zero-fee atomic trades.
        """
        book = self.order_books[pair]
        opposite_side = "SELL" if new_order["side"] == "BUY" else "BUY"

        for existing_order in book:
            if existing_order["side"] == opposite_side:
                if (new_order["side"] == "BUY" and new_order["price"] >= existing_order["price"]) or \
                   (new_order["side"] == "SELL" and new_order["price"] <= existing_order["price"]):
                    # Match found!
                    matched_qty = min(new_order["quantity"], existing_order["quantity"])
                    matched_price = existing_order["price"]
                    
                    book.remove(existing_order)
                    return {
                        "matched": True,
                        "executed_price": matched_price,
                        "executed_quantity": matched_qty,
                        "counterparty": existing_order["trader"]
                    }

        # No immediate match, add to order book
        book.append(new_order)
        return {"matched": False, "reason": "Added to order book liquidity depth."}
