import urllib.request
import json
from typing import Dict, Any, Optional

class TimeProtocolSDK:
    """
    Official Python SDK for TIME Protocol Core v2.0.0-Sovereign.
    Provides synchronous and asynchronous wrappers for custodial wallets,
    crypto exchanges (e.g., Bitget, CoinEx), and distributed enterprise applications.
    """
    def __init__(self, api_base_url: str = "http://127.0.0.1:8000"):
        self.api_base_url = api_base_url.rstrip("/")

    def _http_request(self, endpoint: str, method: str = "GET", payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.api_base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        data_bytes = json.dumps(payload).encode("utf-8") if payload else None

        req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise RuntimeError(f"API Error [{e.code}]: {error_body}")

    def get_system_status(self) -> Dict[str, Any]:
        return self._http_request("/v1/status")

    def get_account(self, address: str) -> Dict[str, Any]:
        return self._http_request(f"/v1/account/{address}")

    def propose_transaction(self, address: str, balance: int, nonce: int, staked: int = 0) -> Dict[str, Any]:
        payload = {
            "address": address,
            "balance": balance,
            "nonce": nonce,
            "staked": staked
        }
        return self._http_request("/v1/transaction/propose", method="POST", payload=payload)

    def verify_signature(self, payload: Dict[str, Any], signature: str) -> bool:
        req_payload = {"payload": payload, "signature": signature}
        res = self._http_request("/v1/crypto/verify-signature", method="POST", payload=req_payload)
        return res.get("valid", False)
